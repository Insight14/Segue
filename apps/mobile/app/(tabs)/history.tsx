import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Modal,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { useApiClient } from "../../src/api/context";
import type {
  ConversationResponse,
  ConversationDetailResponse,
} from "../../src/api/types";

export default function HistoryScreen() {
  const client = useApiClient();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);

  // Queries
  const { data: conversations = [], isLoading: isListLoading } = useQuery({
    queryKey: ["conversations", searchQuery],
    queryFn: () => client.listConversations({ q: searchQuery.trim() || undefined }),
  });

  const { data: activeDetail, isLoading: isDetailLoading } = useQuery({
    queryKey: ["conversation", selectedConvId],
    queryFn: () => (selectedConvId ? client.getConversation(selectedConvId) : null),
    enabled: !!selectedConvId,
  });

  // Mutations
  const deleteConvMutation = useMutation({
    mutationFn: (id: string) => client.deleteConversation(id),
    onSuccess: () => {
      setSelectedConvId(null);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err: Error) => Alert.alert("Delete Failed", err.message),
  });

  const rateSuggestionMutation = useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: number }) =>
      client.updateSuggestion(id, { rating }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", selectedConvId] });
    },
    onError: (err: Error) => Alert.alert("Rating Failed", err.message),
  });

  const handleDelete = (id: string) => {
    Alert.alert(
      "Delete Conversation",
      "Are you sure? This will permanently delete the transcript and all associated suggestions (hard delete).",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => deleteConvMutation.mutate(id),
        },
      ]
    );
  };

  const handleExport = async (id: string) => {
    try {
      const payload = await client.exportConversation(id, "json");
      Alert.alert(
        "Export Ready",
        "Conversation exported:\n\n" + payload.slice(0, 200) + "..."
      );
    } catch (err: any) {
      Alert.alert("Export Failed", err.message);
    }
  };

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchBar}>
        <Ionicons name="search-outline" size={18} color="#64748b" />
        <TextInput
          style={styles.searchInput}
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search conversations, contacts, events..."
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery("")}>
            <Ionicons name="close-circle" size={18} color="#94a3b8" />
          </TouchableOpacity>
        )}
      </View>

      {/* Conversations List */}
      {isListLoading ? (
        <View style={styles.emptyContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.listContent}>
          {conversations.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="time-outline" size={48} color="#cbd5e1" />
              <Text style={styles.emptyText}>No past conversations found</Text>
            </View>
          ) : (
            conversations.map((conv: ConversationResponse) => (
              <TouchableOpacity
                key={conv.id}
                style={styles.card}
                onPress={() => setSelectedConvId(conv.id)}
              >
                <View style={styles.cardHeader}>
                  <Text style={styles.contactName}>
                    {conv.summary ? conv.summary.slice(0, 35) + "..." : "Conversation"}
                  </Text>
                  <Text style={styles.dateText}>
                    {new Date(conv.started_at).toLocaleDateString()}
                  </Text>
                </View>

                <Text style={styles.summaryText}>
                  Source: {conv.source} • Status: {conv.ended_at ? "Completed" : "In Progress"}
                </Text>

                <View style={styles.cardFooter}>
                  <Text style={styles.footerInfo}>Tap to view transcript & coach cues</Text>
                  <Ionicons name="chevron-forward" size={16} color="#94a3b8" />
                </View>
              </TouchableOpacity>
            ))
          )}
        </ScrollView>
      )}

      {/* Transcript Detail Modal */}
      {selectedConvId && (
        <Modal visible={!!selectedConvId} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { maxHeight: "90%" }]}>
              {isDetailLoading || !activeDetail ? (
                <View style={styles.centerBox}>
                  <ActivityIndicator size="large" color="#2563eb" />
                </View>
              ) : (
                <>
                  {/* Header */}
                  <View style={styles.modalHeader}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.modalTitle}>
                        {activeDetail.contact?.name || "Conversation Details"}
                      </Text>
                      <Text style={styles.modalSubtitle}>
                        {new Date(activeDetail.started_at).toLocaleString()}{" "}
                        {activeDetail.event?.name ? `• ${activeDetail.event.name}` : ""}
                      </Text>
                    </View>
                    <View style={styles.modalHeaderActions}>
                      <TouchableOpacity
                        style={styles.actionIcon}
                        onPress={() => handleExport(activeDetail.id)}
                      >
                        <Ionicons name="share-outline" size={20} color="#2563eb" />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.actionIcon}
                        onPress={() => handleDelete(activeDetail.id)}
                      >
                        <Ionicons name="trash-outline" size={20} color="#ef4444" />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.actionIcon}
                        onPress={() => setSelectedConvId(null)}
                      >
                        <Ionicons name="close" size={24} color="#64748b" />
                      </TouchableOpacity>
                    </View>
                  </View>

                  {/* Transcript & Suggestions */}
                  <ScrollView style={styles.transcriptScroll}>
                    {activeDetail.summary && (
                      <View style={styles.summaryCard}>
                        <Text style={styles.summaryTitle}>Summary</Text>
                        <Text style={styles.summaryBody}>{activeDetail.summary}</Text>
                      </View>
                    )}

                    <Text style={styles.transcriptSection}>Transcript</Text>
                    {activeDetail.messages.length === 0 ? (
                      <Text style={styles.emptyDetailText}>No messages recorded.</Text>
                    ) : (
                      activeDetail.messages.map((m) => {
                        const matchingSuggestions = activeDetail.suggestions.filter(
                          (s) => s.after_message_seq === m.seq
                        );

                        return (
                          <View key={m.id} style={styles.turnContainer}>
                            <View
                              style={[
                                styles.messageBubble,
                                m.speaker === "user"
                                  ? styles.userBubble
                                  : styles.partnerBubble,
                              ]}
                            >
                              <Text style={styles.speakerLabel}>
                                {m.speaker === "user" ? "You" : "Partner"}
                              </Text>
                              <Text
                                style={[
                                  styles.messageText,
                                  m.speaker === "user" && { color: "#ffffff" },
                                ]}
                              >
                                {m.text}
                              </Text>
                            </View>

                            {/* Live coach suggestions */}
                            {matchingSuggestions.map((sug) => (
                              <View key={sug.id} style={styles.suggestionBox}>
                                <View style={styles.suggestionHeader}>
                                  <Ionicons name="bulb-outline" size={16} color="#d97706" />
                                  <Text style={styles.suggestionTitle}>
                                    Live Coach Suggestion
                                  </Text>
                                </View>
                                <Text style={styles.suggestionText}>{sug.text}</Text>

                                {/* 1-5 Star Rating */}
                                <View style={styles.ratingRow}>
                                  <Text style={styles.ratingLabel}>Rate suggestion:</Text>
                                  {[1, 2, 3, 4, 5].map((star) => (
                                    <TouchableOpacity
                                      key={star}
                                      onPress={() =>
                                        rateSuggestionMutation.mutate({
                                          id: sug.id,
                                          rating: star,
                                        })
                                      }
                                    >
                                      <Ionicons
                                        name={
                                          sug.rating && star <= sug.rating
                                            ? "star"
                                            : "star-outline"
                                        }
                                        size={18}
                                        color="#f59e0b"
                                      />
                                    </TouchableOpacity>
                                  ))}
                                </View>
                              </View>
                            ))}
                          </View>
                        );
                      })
                    )}
                  </ScrollView>
                </>
              )}
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8fafc" },
  centerBox: { padding: 40, alignItems: "center" },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    margin: 16,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    gap: 8,
  },
  searchInput: { flex: 1, fontSize: 14, color: "#0f172a" },
  listContent: { padding: 16, paddingTop: 8 },
  emptyContainer: { alignItems: "center", justifyContent: "center", marginTop: 60 },
  emptyText: { marginTop: 12, fontSize: 14, color: "#94a3b8" },
  emptyDetailText: { fontSize: 13, color: "#94a3b8", fontStyle: "italic", marginVertical: 8 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  contactName: { fontSize: 15, fontWeight: "600", color: "#0f172a", flex: 1, marginRight: 8 },
  dateText: { fontSize: 12, color: "#64748b" },
  summaryText: { fontSize: 13, color: "#475569", marginTop: 6, lineHeight: 18 },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9",
  },
  footerInfo: { fontSize: 12, color: "#94a3b8" },
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
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9",
    paddingBottom: 12,
  },
  modalTitle: { fontSize: 18, fontWeight: "700", color: "#0f172a" },
  modalSubtitle: { fontSize: 13, color: "#64748b", marginTop: 2 },
  modalHeaderActions: { flexDirection: "row", alignItems: "center", gap: 12 },
  actionIcon: { padding: 4 },
  summaryCard: {
    backgroundColor: "#f1f5f9",
    padding: 10,
    borderRadius: 8,
    marginBottom: 14,
  },
  summaryTitle: { fontSize: 12, fontWeight: "700", color: "#334155", marginBottom: 2 },
  summaryBody: { fontSize: 13, color: "#1e293b", lineHeight: 18 },
  transcriptScroll: { maxHeight: "80%" },
  transcriptSection: { fontSize: 15, fontWeight: "700", color: "#1e293b", marginBottom: 12 },
  turnContainer: { marginBottom: 14 },
  messageBubble: {
    maxWidth: "85%",
    borderRadius: 12,
    padding: 10,
    marginBottom: 6,
  },
  userBubble: {
    backgroundColor: "#2563eb",
    alignSelf: "flex-end",
    borderBottomRightRadius: 2,
  },
  partnerBubble: {
    backgroundColor: "#f1f5f9",
    alignSelf: "flex-start",
    borderBottomLeftRadius: 2,
  },
  speakerLabel: { fontSize: 11, fontWeight: "700", color: "#64748b", marginBottom: 2 },
  messageText: { fontSize: 14, color: "#1e293b", lineHeight: 20 },
  suggestionBox: {
    backgroundColor: "#fffbeb",
    borderWidth: 1,
    borderColor: "#fde68a",
    borderRadius: 8,
    padding: 10,
    marginTop: 6,
    marginHorizontal: 12,
  },
  suggestionHeader: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 },
  suggestionTitle: { fontSize: 12, fontWeight: "700", color: "#b45309" },
  suggestionText: { fontSize: 13, color: "#78350f", lineHeight: 18 },
  ratingRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 8 },
  ratingLabel: { fontSize: 12, color: "#92400e" },
});
