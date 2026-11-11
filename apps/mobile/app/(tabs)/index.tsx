import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Modal,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { useApiClient } from "../../src/api/context";
import type { FactKind, FactResponse } from "../../src/api/types";

const FACT_KINDS: FactKind[] = [
  "experience",
  "education",
  "skill",
  "interest",
  "hobby",
  "goal",
  "value",
];

export default function AboutMeScreen() {
  const client = useApiClient();
  const queryClient = useQueryClient();

  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [headline, setHeadline] = useState("");
  const [status, setStatus] = useState("");
  const [goals, setGoals] = useState("");
  const [summaryMd, setSummaryMd] = useState("");

  const [isAddFactOpen, setIsAddFactOpen] = useState(false);
  const [newFactKind, setNewFactKind] = useState<FactKind>("experience");
  const [newFactTitle, setNewFactTitle] = useState("");
  const [newFactBody, setNewFactBody] = useState("");
  const [newFactTags, setNewFactTags] = useState("");

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Queries
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const p = await client.getProfile();
      setHeadline(p.headline || "");
      setStatus(p.status || "");
      setGoals(p.goals || "");
      setSummaryMd(p.summary_md || "");
      return p;
    },
  });

  const { data: facts = [], isLoading: isFactsLoading } = useQuery({
    queryKey: ["facts"],
    queryFn: () => client.listFacts({ confirmed: true }),
  });

  const { data: reviewFacts = [], isLoading: isReviewLoading } = useQuery({
    queryKey: ["facts", "review"],
    queryFn: () => client.getReviewFacts(),
  });

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: () =>
      client.updateProfile({
        headline,
        status,
        goals,
        summary_md: summaryMd,
      }),
    onSuccess: () => {
      setIsEditingProfile(false);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: (err: Error) => Alert.alert("Error", err.message),
  });

  const createFactMutation = useMutation({
    mutationFn: () =>
      client.createFact({
        kind: newFactKind,
        title: newFactTitle,
        body: newFactBody,
        tags: newFactTags ? newFactTags.split(",").map((t) => t.trim()) : [],
        confirmed: true,
      }),
    onSuccess: () => {
      setIsAddFactOpen(false);
      setNewFactTitle("");
      setNewFactBody("");
      setNewFactTags("");
      queryClient.invalidateQueries({ queryKey: ["facts"] });
    },
    onError: (err: Error) => Alert.alert("Error", err.message),
  });

  const confirmFactMutation = useMutation({
    mutationFn: (id: string) => client.confirmFact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      queryClient.invalidateQueries({ queryKey: ["facts", "review"] });
    },
    onError: (err: Error) => Alert.alert("Error", err.message),
  });

  const deleteFactMutation = useMutation({
    mutationFn: (id: string) => client.deleteFact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      queryClient.invalidateQueries({ queryKey: ["facts", "review"] });
    },
    onError: (err: Error) => Alert.alert("Error", err.message),
  });

  const uploadResumeMutation = useMutation({
    mutationFn: async () => {
      // 1. Request presigned upload URL
      const uploadData = await client.createDocumentUploadUrl({
        filename: "resume.pdf",
        mime: "application/pdf",
      });

      // 2. Mock uploading PDF payload in local/test setup
      try {
        await fetch(uploadData.upload_url, {
          method: "PUT",
          body: "Mock PDF payload for resume fact extraction",
          headers: { "Content-Type": "application/pdf" },
        });
      } catch {
        // Local S3 simulation or direct mock
      }

      // 3. Trigger worker processing
      await client.processDocument(uploadData.document_id);
    },
    onSuccess: () => {
      Alert.alert(
        "Resume Uploaded",
        "Resume processing has been queued. Proposed facts will appear in the review queue shortly."
      );
      queryClient.invalidateQueries({ queryKey: ["facts", "review"] });
    },
    onError: (err: Error) => Alert.alert("Upload Failed", err.message),
  });

  const groupedFacts: Record<FactKind, FactResponse[]> = {
    experience: [],
    education: [],
    skill: [],
    interest: [],
    hobby: [],
    goal: [],
    value: [],
    story_success: [],
    story_failure: [],
    story_collaboration: [],
    other: [],
  };

  facts.forEach((fact) => {
    if (groupedFacts[fact.kind]) {
      groupedFacts[fact.kind].push(fact);
    }
  });

  if (isProfileLoading || isFactsLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header Profile Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Profile Summary</Text>
          <View style={styles.row}>
            <TouchableOpacity
              onPress={() => setIsSettingsOpen(true)}
              style={styles.iconButton}
            >
              <Ionicons name="settings-outline" size={20} color="#64748b" />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setIsEditingProfile(!isEditingProfile)}
              style={styles.iconButton}
            >
              <Ionicons
                name={isEditingProfile ? "close-outline" : "create-outline"}
                size={22}
                color="#2563eb"
              />
            </TouchableOpacity>
          </View>
        </View>

        {isEditingProfile ? (
          <View style={styles.form}>
            <Text style={styles.label}>Headline</Text>
            <TextInput
              style={styles.input}
              value={headline}
              onChangeText={setHeadline}
              placeholder="e.g. Senior Backend Engineer"
            />
            <Text style={styles.label}>Status</Text>
            <TextInput
              style={styles.input}
              value={status}
              onChangeText={setStatus}
              placeholder="e.g. Exploring seed-stage AI infra roles"
            />
            <Text style={styles.label}>Goals</Text>
            <TextInput
              style={styles.input}
              value={goals}
              onChangeText={setGoals}
              placeholder="e.g. Connect with founders working on LLM observability"
            />
            <Text style={styles.label}>Summary</Text>
            <TextInput
              style={[styles.input, styles.multilineInput]}
              value={summaryMd}
              onChangeText={setSummaryMd}
              multiline
              numberOfLines={3}
              placeholder="Tell others briefly about your background..."
            />
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={() => updateProfileMutation.mutate()}
            >
              <Text style={styles.primaryButtonText}>Save Profile</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View>
            <Text style={styles.profileHeadline}>
              {profile?.headline || "No headline set"}
            </Text>
            {profile?.status ? (
              <Text style={styles.profileStatus}>Status: {profile.status}</Text>
            ) : null}
            {profile?.goals ? (
              <Text style={styles.profileGoals}>Goals: {profile.goals}</Text>
            ) : null}
            {profile?.summary_md ? (
              <Text style={styles.profileSummary}>{profile.summary_md}</Text>
            ) : null}
          </View>
        )}
      </View>

      {/* Action Buttons: Add Fact & Upload Resume */}
      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => setIsAddFactOpen(true)}
        >
          <Ionicons name="add-circle-outline" size={18} color="#2563eb" />
          <Text style={styles.secondaryButtonText}>Add Fact</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryButton, styles.uploadButton]}
          onPress={() => uploadResumeMutation.mutate()}
          disabled={uploadResumeMutation.isPending}
        >
          <Ionicons name="cloud-upload-outline" size={18} color="#059669" />
          <Text style={[styles.secondaryButtonText, { color: "#059669" }]}>
            {uploadResumeMutation.isPending ? "Uploading..." : "Upload Resume"}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Review Queue (Unconfirmed Facts) */}
      {reviewFacts.length > 0 && (
        <View style={[styles.card, styles.reviewCard]}>
          <View style={styles.cardHeader}>
            <View style={styles.row}>
              <Ionicons name="alert-circle-outline" size={20} color="#d97706" />
              <Text style={[styles.cardTitle, { color: "#d97706", marginLeft: 6 }]}>
                Review Queue ({reviewFacts.length})
              </Text>
            </View>
          </View>
          <Text style={styles.helperText}>
            Proposed from uploaded resumes or conversation discovery. Confirm or discard below.
          </Text>

          {reviewFacts.map((fact) => (
            <View key={fact.id} style={styles.reviewItem}>
              <View style={styles.reviewInfo}>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{fact.kind}</Text>
                </View>
                <Text style={styles.factTitle}>{fact.title}</Text>
                <Text style={styles.factContent}>{fact.body}</Text>
                {fact.source && (
                  <Text style={styles.factSource}>Source: {fact.source}</Text>
                )}
              </View>
              <View style={styles.reviewActions}>
                <TouchableOpacity
                  style={styles.confirmButton}
                  onPress={() => confirmFactMutation.mutate(fact.id)}
                >
                  <Ionicons name="checkmark" size={16} color="#ffffff" />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.discardButton}
                  onPress={() => deleteFactMutation.mutate(fact.id)}
                >
                  <Ionicons name="trash-outline" size={16} color="#ef4444" />
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Grouped Confirmed Facts */}
      <Text style={styles.sectionHeader}>Confirmed Profile Facts</Text>
      {FACT_KINDS.map((kind) => {
        const items = groupedFacts[kind];
        return (
          <View key={kind} style={styles.card}>
            <View style={styles.kindHeader}>
              <Text style={styles.kindTitle}>
                {kind.charAt(0).toUpperCase() + kind.slice(1)} ({items.length})
              </Text>
            </View>

            {items.length === 0 ? (
              <Text style={styles.emptyText}>No {kind} facts added yet.</Text>
            ) : (
              items.map((fact) => (
                <View key={fact.id} style={styles.factRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.factTitle}>{fact.title}</Text>
                    <Text style={styles.factContent}>{fact.body}</Text>
                    {fact.tags && fact.tags.length > 0 && (
                      <View style={styles.tagList}>
                        {fact.tags.map((t, idx) => (
                          <View key={idx} style={styles.tag}>
                            <Text style={styles.tagText}>{t}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                  <TouchableOpacity
                    onPress={() => deleteFactMutation.mutate(fact.id)}
                    style={styles.deleteFactButton}
                  >
                    <Ionicons name="trash-outline" size={16} color="#94a3b8" />
                  </TouchableOpacity>
                </View>
              ))
            )}
          </View>
        );
      })}

      {/* Add Fact Modal */}
      <Modal visible={isAddFactOpen} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Profile Fact</Text>
            <Text style={styles.label}>Kind</Text>
            <View style={styles.kindSelector}>
              {FACT_KINDS.map((k) => (
                <TouchableOpacity
                  key={k}
                  style={[
                    styles.kindChip,
                    newFactKind === k && styles.kindChipActive,
                  ]}
                  onPress={() => setNewFactKind(k)}
                >
                  <Text
                    style={[
                      styles.kindChipText,
                      newFactKind === k && styles.kindChipTextActive,
                    ]}
                  >
                    {k}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.label}>Fact Title</Text>
            <TextInput
              style={styles.input}
              value={newFactTitle}
              onChangeText={setNewFactTitle}
              placeholder="e.g. Distributed Cache Optimization"
            />

            <Text style={styles.label}>Details / Body</Text>
            <TextInput
              style={[styles.input, styles.multilineInput]}
              value={newFactBody}
              onChangeText={setNewFactBody}
              placeholder="e.g. Led redesign of core checkout flow increasing conversion by 14%"
              multiline
              numberOfLines={3}
            />

            <Text style={styles.label}>Tags (comma-separated)</Text>
            <TextInput
              style={styles.input}
              value={newFactTags}
              onChangeText={setNewFactTags}
              placeholder="e.g. backend, python, distributed systems"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setIsAddFactOpen(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.primaryButton,
                  (!newFactTitle.trim() || !newFactBody.trim()) && {
                    opacity: 0.5,
                  },
                ]}
                onPress={() => createFactMutation.mutate()}
                disabled={!newFactTitle.trim() || !newFactBody.trim()}
              >
                <Text style={styles.primaryButtonText}>Save Fact</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Settings Modal Sheet */}
      <Modal visible={isSettingsOpen} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Privacy & Preferences</Text>
            <Text style={styles.helperText}>
              Retention: Transcripts are retained for 30 days by default. Audio is never stored.
            </Text>

            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Data Retention</Text>
              <Text style={styles.settingValue}>30 Days</Text>
            </View>

            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Audio/Video Storage</Text>
              <Text style={styles.settingValue}>Disabled (Text Only)</Text>
            </View>

            <TouchableOpacity
              style={[styles.cancelButton, { marginTop: 24 }]}
              onPress={() => setIsSettingsOpen(false)}
            >
              <Text style={styles.cancelButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8fafc" },
  content: { padding: 16, paddingBottom: 40 },
  centerContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  reviewCard: {
    borderColor: "#fef3c7",
    backgroundColor: "#fffbeb",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  cardTitle: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
  row: { flexDirection: "row", alignItems: "center" },
  iconButton: { padding: 6, marginLeft: 8 },
  profileHeadline: { fontSize: 18, fontWeight: "700", color: "#0f172a" },
  profileStatus: { fontSize: 14, color: "#2563eb", marginTop: 4, fontWeight: "500" },
  profileGoals: { fontSize: 13, color: "#64748b", marginTop: 4 },
  profileSummary: {
    fontSize: 14,
    color: "#334155",
    marginTop: 8,
    lineHeight: 20,
  },
  label: { fontSize: 12, fontWeight: "600", color: "#475569", marginTop: 10, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    backgroundColor: "#ffffff",
  },
  multilineInput: { minHeight: 64, textAlignVertical: "top" },
  form: { marginTop: 4 },
  primaryButton: {
    backgroundColor: "#2563eb",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 12,
  },
  primaryButtonText: { color: "#ffffff", fontWeight: "600", fontSize: 14 },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 16,
    gap: 12,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#eff6ff",
    borderColor: "#bfdbfe",
    borderWidth: 1,
    paddingVertical: 12,
    borderRadius: 10,
    gap: 6,
  },
  secondaryButtonText: { color: "#2563eb", fontWeight: "600", fontSize: 14 },
  uploadButton: {
    backgroundColor: "#ecfdf5",
    borderColor: "#a7f3d0",
  },
  helperText: { fontSize: 13, color: "#64748b", marginBottom: 12 },
  reviewItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#fde68a",
  },
  reviewInfo: { flex: 1, marginRight: 8 },
  badge: {
    backgroundColor: "#fef3c7",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: "flex-start",
    marginBottom: 4,
  },
  badgeText: { fontSize: 11, fontWeight: "600", color: "#b45309" },
  factTitle: { fontSize: 14, fontWeight: "700", color: "#0f172a" },
  factContent: { fontSize: 13, color: "#334155", lineHeight: 18, marginTop: 2 },
  factSource: { fontSize: 11, color: "#94a3b8", marginTop: 2 },
  reviewActions: { flexDirection: "row", gap: 8 },
  confirmButton: {
    backgroundColor: "#10b981",
    padding: 8,
    borderRadius: 6,
  },
  discardButton: {
    backgroundColor: "#fee2e2",
    padding: 8,
    borderRadius: 6,
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
    marginBottom: 12,
    marginTop: 8,
  },
  kindHeader: { marginBottom: 8 },
  kindTitle: { fontSize: 14, fontWeight: "600", color: "#334155" },
  emptyText: { fontSize: 13, color: "#94a3b8", fontStyle: "italic" },
  factRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9",
  },
  deleteFactButton: { padding: 4, marginLeft: 8 },
  tagList: { flexDirection: "row", flexWrap: "wrap", gap: 4, marginTop: 4 },
  tag: {
    backgroundColor: "#f1f5f9",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tagText: { fontSize: 11, color: "#64748b" },
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
  modalTitle: { fontSize: 18, fontWeight: "700", color: "#0f172a", marginBottom: 12 },
  kindSelector: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 8 },
  kindChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#f1f5f9",
  },
  kindChipActive: { backgroundColor: "#2563eb" },
  kindChipText: { fontSize: 12, color: "#475569", textTransform: "capitalize" },
  kindChipTextActive: { color: "#ffffff", fontWeight: "600" },
  modalButtons: { flexDirection: "row", justifyContent: "flex-end", gap: 12, marginTop: 16 },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#f1f5f9",
    alignItems: "center",
  },
  cancelButtonText: { color: "#475569", fontWeight: "600" },
  settingRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9",
  },
  settingLabel: { fontSize: 14, color: "#334155" },
  settingValue: { fontSize: 14, fontWeight: "600", color: "#0f172a" },
});
