import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Alert,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { useApiClient } from "../../src/api/context";
import type {
  ThreadMode,
  ThreadResponse,
  TalkingPointsResponse,
} from "../../src/api/types";

export default function CoachScreen() {
  const client = useApiClient();
  const queryClient = useQueryClient();
  const scrollViewRef = useRef<ScrollView>(null);

  const [mode, setMode] = useState<ThreadMode>("discover");
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [isSending, setIsSending] = useState(false);

  // Talking points modal state
  const [isPrepModalOpen, setIsPrepModalOpen] = useState(false);
  const [notes, setNotes] = useState("");
  const [selectedTalkingPoints, setSelectedTalkingPoints] =
    useState<TalkingPointsResponse | null>(null);

  // List threads
  const { data: threads = [], isLoading: isThreadsLoading } = useQuery({
    queryKey: ["agent", "threads"],
    queryFn: () => client.listThreads(),
  });

  // Select or initialize thread for current mode
  useEffect(() => {
    const matchingThread = threads.find((t) => t.mode === mode);
    if (matchingThread) {
      setActiveThreadId(matchingThread.id);
    } else if (!isThreadsLoading && !activeThreadId) {
      // Create initial thread
      createThreadMutation.mutate(mode);
    }
  }, [mode, threads, isThreadsLoading]);

  // Fetch active thread detail
  const { data: activeThread, refetch: refetchActiveThread } = useQuery({
    queryKey: ["agent", "thread", activeThreadId],
    queryFn: () => (activeThreadId ? client.getThread(activeThreadId) : null),
    enabled: !!activeThreadId,
  });

  // Mutations
  const createThreadMutation = useMutation({
    mutationFn: (newMode: ThreadMode) =>
      client.createThread({
        mode: newMode,
        title: `${newMode === "discover" ? "Discovery" : "Preparation"} Session`,
      }),
    onSuccess: (newThread: ThreadResponse) => {
      setActiveThreadId(newThread.id);
      queryClient.invalidateQueries({ queryKey: ["agent", "threads"] });
    },
  });

  const generateTalkingPointsMutation = useMutation({
    mutationFn: () =>
      client.generateTalkingPoints({
        notes: notes.trim() || undefined,
      }),
    onSuccess: (tp: TalkingPointsResponse) => {
      setIsPrepModalOpen(false);
      setNotes("");
      setSelectedTalkingPoints(tp);
      queryClient.invalidateQueries({ queryKey: ["talking-points"] });
    },
    onError: (err: Error) => Alert.alert("Generation Failed", err.message),
  });

  const handleSendMessage = async () => {
    if (!inputText.trim() || !activeThreadId || isSending) return;

    const userMsg = inputText.trim();
    setInputText("");
    setIsSending(true);
    setStreamingText("");

    try {
      // In mobile environment, we call the messages SSE endpoint
      const response = await fetch(
        `${(client as any).baseUrl}/v1/agent/threads/${activeThreadId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${await (client as any).getAuthToken?.()}`,
          },
          body: JSON.stringify({ content: userMsg }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      // Read SSE stream
      const text = await response.text();
      const lines = text.split("\n");
      let fullAssistantMessage = "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.slice(6).trim();
          if (dataStr === "[DONE]") break;
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.chunk) {
              fullAssistantMessage += parsed.chunk;
              setStreamingText(fullAssistantMessage);
            }
          } catch {
            // non-json chunk
          }
        }
      }

      setStreamingText("");
      await refetchActiveThread();
      queryClient.invalidateQueries({ queryKey: ["facts", "review"] });
    } catch (err: any) {
      Alert.alert("Error sending message", err.message);
    } finally {
      setIsSending(false);
    }
  };

  const handleSwitchMode = (newMode: ThreadMode) => {
    if (newMode === mode) return;
    setMode(newMode);
    const existing = threads.find((t) => t.mode === newMode);
    if (existing) {
      setActiveThreadId(existing.id);
    } else {
      createThreadMutation.mutate(newMode);
    }
  };

  return (
    <View style={styles.container}>
      {/* Top Bar: Mode Switcher & Talking Points Action */}
      <View style={styles.topBar}>
        <View style={styles.modeSwitch}>
          <TouchableOpacity
            style={[
              styles.modeTab,
              mode === "discover" && styles.modeTabActive,
            ]}
            onPress={() => handleSwitchMode("discover")}
          >
            <Ionicons
              name="compass-outline"
              size={16}
              color={mode === "discover" ? "#2563eb" : "#64748b"}
            />
            <Text
              style={[
                styles.modeTabText,
                mode === "discover" && styles.modeTabTextActive,
              ]}
            >
              Discover
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.modeTab, mode === "prep" && styles.modeTabActive]}
            onPress={() => handleSwitchMode("prep")}
          >
            <Ionicons
              name="sparkles-outline"
              size={16}
              color={mode === "prep" ? "#2563eb" : "#64748b"}
            />
            <Text
              style={[
                styles.modeTabText,
                mode === "prep" && styles.modeTabTextActive,
              ]}
            >
              Prep
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.tpButton}
          onPress={() => setIsPrepModalOpen(true)}
        >
          <Ionicons name="document-text-outline" size={16} color="#ffffff" />
          <Text style={styles.tpButtonText}>Talking Points</Text>
        </TouchableOpacity>
      </View>

      {/* Messages Stream */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        onContentSizeChange={() =>
          scrollViewRef.current?.scrollToEnd({ animated: true })
        }
      >
        {activeThread?.messages.map((msg) => (
          <View
            key={msg.id}
            style={[
              styles.messageBubble,
              msg.role === "user" ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text
              style={[
                styles.messageText,
                msg.role === "user"
                  ? styles.userMessageText
                  : styles.assistantMessageText,
              ]}
            >
              {msg.content}
            </Text>
          </View>
        ))}

        {streamingText ? (
          <View style={[styles.messageBubble, styles.assistantBubble]}>
            <Text style={[styles.messageText, styles.assistantMessageText]}>
              {streamingText}
            </Text>
          </View>
        ) : null}

        {isSending && !streamingText && (
          <View style={styles.typingIndicator}>
            <ActivityIndicator size="small" color="#2563eb" />
            <Text style={styles.typingText}>Coach is thinking...</Text>
          </View>
        )}
      </ScrollView>

      {/* Input Bar */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.chatInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder={
            mode === "discover"
              ? "Answer the coach's question..."
              : "Ask about interview prep or company notes..."
          }
          multiline
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!inputText.trim() || isSending) && styles.sendButtonDisabled,
          ]}
          onPress={handleSendMessage}
          disabled={!inputText.trim() || isSending}
        >
          <Ionicons name="send" size={18} color="#ffffff" />
        </TouchableOpacity>
      </View>

      {/* Make Talking Points Modal */}
      <Modal visible={isPrepModalOpen} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Generate Talking Points</Text>
            <Text style={styles.helperText}>
              The prep agent grounds every claim in your confirmed profile facts
              and produces 30s elevator pitches, STAR stories, questions, and
              icebreakers.
            </Text>

            <Text style={styles.label}>Context / Notes (Optional)</Text>
            <TextInput
              style={[styles.chatInput, styles.notesInput]}
              value={notes}
              onChangeText={setNotes}
              placeholder="e.g. Coffee chat with VP of Eng at Stripe discussing infra scale"
              multiline
              numberOfLines={4}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setIsPrepModalOpen(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.generateButton}
                onPress={() => generateTalkingPointsMutation.mutate()}
                disabled={generateTalkingPointsMutation.isPending}
              >
                {generateTalkingPointsMutation.isPending ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <Text style={styles.generateButtonText}>Generate</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Talking Points Result Modal */}
      {selectedTalkingPoints && (
        <Modal visible={!!selectedTalkingPoints} transparent animationType="fade">
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { maxHeight: "90%" }]}>
              <View style={styles.cardHeader}>
                <Text style={styles.modalTitle}>Your Talking Points</Text>
                <TouchableOpacity
                  onPress={() => setSelectedTalkingPoints(null)}
                >
                  <Ionicons name="close" size={24} color="#64748b" />
                </TouchableOpacity>
              </View>

              <ScrollView>
                <Text style={styles.tpSectionHeader}>30-Second Pitch</Text>
                <Text style={styles.tpBodyText}>
                  {selectedTalkingPoints.content.pitch_30s}
                </Text>

                {selectedTalkingPoints.content.stories?.length > 0 && (
                  <>
                    <Text style={styles.tpSectionHeader}>STAR Stories</Text>
                    {selectedTalkingPoints.content.stories.map((s, idx) => (
                      <View key={idx} style={styles.storyCard}>
                        <Text style={styles.storyTitle}>{s.title}</Text>
                        <Text style={styles.storyText}>
                          <Text style={{ fontWeight: "700" }}>Situation: </Text>
                          {s.situation}
                        </Text>
                        <Text style={styles.storyText}>
                          <Text style={{ fontWeight: "700" }}>Action: </Text>
                          {s.action}
                        </Text>
                        <Text style={styles.storyText}>
                          <Text style={{ fontWeight: "700" }}>Result: </Text>
                          {s.result}
                        </Text>
                      </View>
                    ))}
                  </>
                )}

                {selectedTalkingPoints.content.icebreakers?.length > 0 && (
                  <>
                    <Text style={styles.tpSectionHeader}>Icebreakers</Text>
                    {selectedTalkingPoints.content.icebreakers.map((ib, idx) => (
                      <Text key={idx} style={styles.bulletText}>
                        • {ib}
                      </Text>
                    ))}
                  </>
                )}

                {selectedTalkingPoints.content.questions_to_ask?.length > 0 && (
                  <>
                    <Text style={styles.tpSectionHeader}>Questions to Ask</Text>
                    {selectedTalkingPoints.content.questions_to_ask.map(
                      (q, idx) => (
                        <Text key={idx} style={styles.bulletText}>
                          • {q}
                        </Text>
                      )
                    )}
                  </>
                )}

                {selectedTalkingPoints.content.if_asked_about_weakness && (
                  <>
                    <Text style={styles.tpSectionHeader}>
                      If Asked About Weakness
                    </Text>
                    <Text style={styles.tpBodyText}>
                      {selectedTalkingPoints.content.if_asked_about_weakness}
                    </Text>
                  </>
                )}

                {selectedTalkingPoints.content.gaps?.length > 0 && (
                  <>
                    <Text style={[styles.tpSectionHeader, { color: "#d97706" }]}>
                      Identified Gaps
                    </Text>
                    {selectedTalkingPoints.content.gaps.map((g, idx) => (
                      <Text key={idx} style={[styles.bulletText, { color: "#b45309" }]}>
                        ! {g}
                      </Text>
                    ))}
                  </>
                )}
              </ScrollView>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8fafc" },
  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  modeSwitch: {
    flexDirection: "row",
    backgroundColor: "#f1f5f9",
    borderRadius: 8,
    padding: 2,
  },
  modeTab: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    gap: 4,
  },
  modeTabActive: {
    backgroundColor: "#ffffff",
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 2,
    elevation: 1,
  },
  modeTabText: { fontSize: 13, color: "#64748b", fontWeight: "500" },
  modeTabTextActive: { color: "#2563eb", fontWeight: "600" },
  tpButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2563eb",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    gap: 4,
  },
  tpButtonText: { color: "#ffffff", fontSize: 13, fontWeight: "600" },
  messagesContainer: { flex: 1 },
  messagesContent: { padding: 16, paddingBottom: 20 },
  messageBubble: {
    maxWidth: "80%",
    borderRadius: 14,
    padding: 12,
    marginBottom: 10,
  },
  userBubble: {
    backgroundColor: "#2563eb",
    alignSelf: "flex-end",
    borderBottomRightRadius: 2,
  },
  assistantBubble: {
    backgroundColor: "#ffffff",
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderBottomLeftRadius: 2,
  },
  messageText: { fontSize: 14, lineHeight: 20 },
  userMessageText: { color: "#ffffff" },
  assistantMessageText: { color: "#0f172a" },
  typingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 8,
  },
  typingText: { fontSize: 13, color: "#64748b", fontStyle: "italic" },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    padding: 10,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    gap: 8,
  },
  chatInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    maxHeight: 100,
    fontSize: 14,
    backgroundColor: "#ffffff",
  },
  sendButton: {
    backgroundColor: "#2563eb",
    padding: 10,
    borderRadius: 20,
  },
  sendButtonDisabled: { opacity: 0.4 },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "flex-end",
  },
  modalContent: {
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 20,
    maxHeight: "85%",
  },
  modalTitle: { fontSize: 18, fontWeight: "700", color: "#0f172a", marginBottom: 8 },
  helperText: { fontSize: 13, color: "#64748b", marginBottom: 12, lineHeight: 18 },
  label: { fontSize: 12, fontWeight: "600", color: "#475569", marginTop: 8, marginBottom: 4 },
  notesInput: {
    borderRadius: 8,
    minHeight: 80,
    textAlignVertical: "top",
  },
  modalButtons: { flexDirection: "row", justifyContent: "flex-end", gap: 12, marginTop: 16 },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#f1f5f9",
  },
  cancelButtonText: { color: "#475569", fontWeight: "600" },
  generateButton: {
    backgroundColor: "#2563eb",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  generateButtonText: { color: "#ffffff", fontWeight: "600" },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  tpSectionHeader: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1e293b",
    marginTop: 14,
    marginBottom: 6,
  },
  tpBodyText: { fontSize: 14, color: "#334155", lineHeight: 20 },
  storyCard: {
    backgroundColor: "#f8fafc",
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: "#2563eb",
  },
  storyTitle: { fontSize: 14, fontWeight: "700", color: "#0f172a", marginBottom: 4 },
  storyText: { fontSize: 13, color: "#334155", marginTop: 2, lineHeight: 18 },
  bulletText: { fontSize: 14, color: "#334155", marginVertical: 3, lineHeight: 20 },
});
