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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface MockMessage {
  id: string;
  speaker: "user" | "partner";
  text: string;
  seq: number;
}

interface MockSuggestion {
  id: string;
  after_message_seq: number;
  text: string;
  shown: boolean;
  selected: boolean;
  rating: number | null;
}

interface ConversationItem {
  id: string;
  contact_name: string;
  event_name?: string;
  date: string;
  summary: string;
  messages: MockMessage[];
  suggestions: MockSuggestion[];
}

const INITIAL_CONVERSATIONS: ConversationItem[] = [
  {
    id: "conv-1",
    contact_name: "Sarah Jenkins (Acme Corp)",
    event_name: "Tech Meetup 2026",
    date: "2026-11-10",
    summary: "Discussed distributed caching challenges and Redis clustering",
    messages: [
      { id: "m1", seq: 1, speaker: "partner", text: "Hey! What kind of backend stack are you working with lately?" },
      { id: "m2", seq: 2, speaker: "user", text: "Mostly Python and FastAPI with Redis caching layers." },
      { id: "m3", seq: 3, speaker: "partner", text: "Nice! Have you ever had to deal with cache stampedes under high concurrency?" },
    ],
    suggestions: [
      {
        id: "s1",
        after_message_seq: 3,
        text: "Mention your experience using Redis mutex locks to prevent stampedes",
        shown: true,
        selected: true,
        rating: 5,
      },
    ],
  },
];

export default function HistoryScreen() {
  const [conversations, setConversations] =
    useState<ConversationItem[]>(INITIAL_CONVERSATIONS);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConv, setSelectedConv] = useState<ConversationItem | null>(null);

  const filteredConversations = conversations.filter(
    (c) =>
      c.contact_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.event_name && c.event_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleDelete = (id: string) => {
    Alert.alert(
      "Delete Conversation",
      "Are you sure? This will permanently delete the transcript and all associated suggestions (hard delete).",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => {
            setConversations((prev) => prev.filter((c) => c.id !== id));
            if (selectedConv?.id === id) {
              setSelectedConv(null);
            }
          },
        },
      ]
    );
  };

  const handleExport = (conv: ConversationItem) => {
    const exportJson = JSON.stringify(conv, null, 2);
    Alert.alert("Export Ready", "Conversation exported as JSON payload:\n\n" + exportJson.slice(0, 200) + "...");
  };

  const handleRateSuggestion = (sugId: string, rating: number) => {
    if (!selectedConv) return;
    const updated = {
      ...selectedConv,
      suggestions: selectedConv.suggestions.map((s) =>
        s.id === sugId ? { ...s, rating } : s
      ),
    };
    setSelectedConv(updated);
    setConversations((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
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
      <ScrollView contentContainerStyle={styles.listContent}>
        {filteredConversations.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="time-outline" size={48} color="#cbd5e1" />
            <Text style={styles.emptyText}>No past conversations found</Text>
          </View>
        ) : (
          filteredConversations.map((conv) => (
            <TouchableOpacity
              key={conv.id}
              style={styles.card}
              onPress={() => setSelectedConv(conv)}
            >
              <View style={styles.cardHeader}>
                <Text style={styles.contactName}>{conv.contact_name}</Text>
                <Text style={styles.dateText}>{conv.date}</Text>
              </View>

              {conv.event_name && (
                <Text style={styles.eventName}>Event: {conv.event_name}</Text>
              )}

              <Text style={styles.summaryText}>{conv.summary}</Text>

              <View style={styles.cardFooter}>
                <Text style={styles.footerInfo}>
                  {conv.messages.length} messages • {conv.suggestions.length} suggestions
                </Text>
                <Ionicons name="chevron-forward" size={16} color="#94a3b8" />
              </View>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      {/* Transcript Detail Modal */}
      {selectedConv && (
        <Modal visible={!!selectedConv} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { maxHeight: "90%" }]}>
              {/* Header */}
              <View style={styles.modalHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.modalTitle}>{selectedConv.contact_name}</Text>
                  <Text style={styles.modalSubtitle}>
                    {selectedConv.date} {selectedConv.event_name ? `• ${selectedConv.event_name}` : ""}
                  </Text>
                </View>
                <View style={styles.modalHeaderActions}>
                  <TouchableOpacity
                    style={styles.actionIcon}
                    onPress={() => handleExport(selectedConv)}
                  >
                    <Ionicons name="share-outline" size={20} color="#2563eb" />
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.actionIcon}
                    onPress={() => handleDelete(selectedConv.id)}
                  >
                    <Ionicons name="trash-outline" size={20} color="#ef4444" />
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.actionIcon}
                    onPress={() => setSelectedConv(null)}
                  >
                    <Ionicons name="close" size={24} color="#64748b" />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Transcript & Suggestions */}
              <ScrollView style={styles.transcriptScroll}>
                <Text style={styles.transcriptSection}>Transcript</Text>
                {selectedConv.messages.map((m) => {
                  const matchingSuggestions = selectedConv.suggestions.filter(
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

                      {/* Display live coach suggestions injected after this message */}
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
                                onPress={() => handleRateSuggestion(sug.id, star)}
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
                })}
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
  contactName: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
  dateText: { fontSize: 12, color: "#64748b" },
  eventName: { fontSize: 13, color: "#2563eb", marginTop: 4, fontWeight: "500" },
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
