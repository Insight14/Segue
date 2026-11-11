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
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { useApiClient } from "../../src/api/context";

export default function LiveScreen() {
  const client = useApiClient();
  const queryClient = useQueryClient();

  const [inSession, setInSession] = useState(false);
  const [deviceConnected, setDeviceConnected] = useState(true);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  // Pre-session form
  const [contactName, setContactName] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [notes, setNotes] = useState("");
  const [eventName, setEventName] = useState("");

  // Consent modal
  const [isConsentModalOpen, setIsConsentModalOpen] = useState(false);
  const [consentNoted, setConsentNoted] = useState(false);

  // Live session suggestions state
  const [suggestions, setSuggestions] = useState<string[]>([
    "Ask about their current engineering team size and migration roadmap",
    "Mention your experience with zero-downtime DB migrations in Postgres",
  ]);

  const startSessionMutation = useMutation({
    mutationFn: async () => {
      // 1. Create or link event if provided
      let eventId: string | undefined = undefined;
      if (eventName.trim()) {
        const ev = await client.createEvent({ name: eventName.trim() });
        eventId = ev.id;
      }

      // 2. Create contact
      const contact = await client.createContact({
        name: contactName.trim(),
        company: company.trim() || undefined,
        role: role.trim() || undefined,
        notes: notes.trim() || undefined,
        event_id: eventId,
        consent_noted: true,
      });

      // 3. Create conversation session
      const conv = await client.createConversation({
        contact_id: contact.id,
        event_id: eventId,
        source: "phone",
      });

      return conv;
    },
    onSuccess: (conv) => {
      setActiveConvId(conv.id);
      setIsConsentModalOpen(false);
      setConsentNoted(true);
      setInSession(true);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err: Error) => Alert.alert("Session Error", err.message),
  });

  const endSessionMutation = useMutation({
    mutationFn: async () => {
      if (!activeConvId) return;
      await client.updateConversation(activeConvId, {
        ended_at: new Date().toISOString(),
        summary: `Networking session with ${contactName}`,
      });
    },
    onSuccess: () => {
      setInSession(false);
      setActiveConvId(null);
      setContactName("");
      setCompany("");
      setRole("");
      setNotes("");
      setEventName("");
      setConsentNoted(false);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      Alert.alert("Session Saved", "Conversation transcript saved to your History.");
    },
    onError: (err: Error) => Alert.alert("End Session Failed", err.message),
  });

  const handleStartPrompt = () => {
    if (!contactName.trim()) {
      Alert.alert("Contact Name Required", "Please enter the person's name.");
      return;
    }
    // Show mandatory privacy & consent reminder
    setIsConsentModalOpen(true);
  };

  const handleConfirmConsentAndStart = () => {
    startSessionMutation.mutate();
  };

  const handleStopSession = () => {
    Alert.alert(
      "End Live Session",
      "Are you sure you want to end this conversation? Suggestions and transcript will be saved to your History.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "End Session",
          style: "destructive",
          onPress: () => endSessionMutation.mutate(),
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Device Connection Status Bar */}
      <View style={styles.statusBar}>
        <View style={styles.deviceRow}>
          <View
            style={[
              styles.statusDot,
              { backgroundColor: deviceConnected ? "#10b981" : "#ef4444" },
            ]}
          />
          <Text style={styles.deviceStatusText}>
            Glasses Display:{" "}
            {deviceConnected ? "Connected (USB Serial)" : "Disconnected"}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => setDeviceConnected(!deviceConnected)}
          style={styles.toggleDeviceBtn}
        >
          <Text style={styles.toggleDeviceText}>
            {deviceConnected ? "Simulate Disconnect" : "Connect"}
          </Text>
        </TouchableOpacity>
      </View>

      {!inSession ? (
        /* Pre-Session Setup Card */
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Start a Live Conversation</Text>
          <Text style={styles.helperText}>
            Enter details about the person you are meeting. The Live Coach will
            provide real-time cues (under 80 characters) on your glasses display.
          </Text>

          <Text style={styles.label}>Contact Name *</Text>
          <TextInput
            style={styles.input}
            value={contactName}
            onChangeText={setContactName}
            placeholder="e.g. Jordan Lee"
          />

          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>Company</Text>
              <TextInput
                style={styles.input}
                value={company}
                onChangeText={setCompany}
                placeholder="e.g. Datadog"
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Role</Text>
              <TextInput
                style={styles.input}
                value={role}
                onChangeText={setRole}
                placeholder="e.g. Staff SRE"
              />
            </View>
          </View>

          <Text style={styles.label}>Event (Optional)</Text>
          <TextInput
            style={styles.input}
            value={eventName}
            onChangeText={setEventName}
            placeholder="e.g. KubeCon 2026 / Coffee Chat"
          />

          <Text style={styles.label}>Context / Notes (Optional)</Text>
          <TextInput
            style={[styles.input, styles.multilineInput]}
            value={notes}
            onChangeText={setNotes}
            placeholder="e.g. Looking for engineers with strong Kubernetes operator experience"
            multiline
            numberOfLines={3}
          />

          <TouchableOpacity
            style={styles.startButton}
            onPress={handleStartPrompt}
            disabled={startSessionMutation.isPending}
          >
            {startSessionMutation.isPending ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <>
                <Ionicons name="play-circle" size={20} color="#ffffff" />
                <Text style={styles.startButtonText}>Begin Session</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      ) : (
        /* Active Live Session View */
        <View>
          <View style={[styles.card, styles.activeCard]}>
            <View style={styles.sessionHeader}>
              <View>
                <View style={styles.liveIndicator}>
                  <View style={styles.pulsingDot} />
                  <Text style={styles.liveText}>SESSION IN PROGRESS</Text>
                </View>
                <Text style={styles.activeContactName}>{contactName}</Text>
                <Text style={styles.activeContactMeta}>
                  {role ? `${role} • ` : ""}
                  {company || "Independent"}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.stopButton}
                onPress={handleStopSession}
                disabled={endSessionMutation.isPending}
              >
                {endSessionMutation.isPending ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <>
                    <Ionicons name="stop" size={16} color="#ffffff" />
                    <Text style={styles.stopButtonText}>End</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>

          {/* Current Live Suggestions */}
          <Text style={styles.sectionHeader}>Live Coach Suggestions</Text>
          <Text style={styles.helperText}>
            Top suggestions sent to your glasses HUD (max 3, each &lt;= 80 chars).
          </Text>

          {suggestions.map((sug, idx) => (
            <View key={idx} style={styles.suggestionCard}>
              <View style={styles.suggestionNumber}>
                <Text style={styles.suggestionNumberText}>#{idx + 1}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.suggestionBody}>{sug}</Text>
                <Text style={styles.charCount}>{sug.length} / 80 chars</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Mandatory Consent & Privacy Modal */}
      <Modal visible={isConsentModalOpen} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.consentIconRow}>
              <Ionicons name="shield-checkmark" size={32} color="#2563eb" />
            </View>
            <Text style={styles.consentTitle}>Consent & Privacy Notice</Text>
            <Text style={styles.consentBody}>
              Recording-consent laws differ across jurisdictions (many require
              all-party consent).
              {"\n\n"}
              • Audio is processed in memory and never stored.
              {"\n"}
              • Conversations are stored as text and can be deleted at any time.
              {"\n"}
              • Please confirm that all participants have consented to live
              assistance.
            </Text>

            <TouchableOpacity
              style={styles.consentCheckboxRow}
              onPress={() => setConsentNoted(!consentNoted)}
            >
              <Ionicons
                name={consentNoted ? "checkbox" : "square-outline"}
                size={22}
                color="#2563eb"
              />
              <Text style={styles.consentCheckboxLabel}>
                Consent has been noted for this contact
              </Text>
            </TouchableOpacity>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setIsConsentModalOpen(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.confirmConsentButton,
                  (!consentNoted || startSessionMutation.isPending) && styles.disabledButton,
                ]}
                onPress={handleConfirmConsentAndStart}
                disabled={!consentNoted || startSessionMutation.isPending}
              >
                <Text style={styles.confirmConsentText}>I Understand & Agree</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8fafc" },
  content: { padding: 16, paddingBottom: 40 },
  statusBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#ffffff",
    padding: 12,
    borderRadius: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  deviceRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
  deviceStatusText: { fontSize: 13, fontWeight: "600", color: "#334155" },
  toggleDeviceBtn: { padding: 4 },
  toggleDeviceText: { fontSize: 12, color: "#2563eb" },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  activeCard: {
    borderColor: "#bfdbfe",
    backgroundColor: "#eff6ff",
  },
  cardTitle: { fontSize: 17, fontWeight: "700", color: "#0f172a", marginBottom: 6 },
  helperText: { fontSize: 13, color: "#64748b", marginBottom: 12, lineHeight: 18 },
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
  row: { flexDirection: "row" },
  startButton: {
    backgroundColor: "#2563eb",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 18,
    gap: 6,
  },
  startButtonText: { color: "#ffffff", fontWeight: "700", fontSize: 15 },
  sessionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  liveIndicator: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 },
  pulsingDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#ef4444" },
  liveText: { fontSize: 11, fontWeight: "800", color: "#ef4444", letterSpacing: 0.5 },
  activeContactName: { fontSize: 18, fontWeight: "700", color: "#0f172a" },
  activeContactMeta: { fontSize: 13, color: "#475569", marginTop: 2 },
  stopButton: {
    backgroundColor: "#ef4444",
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    gap: 4,
  },
  stopButtonText: { color: "#ffffff", fontWeight: "700", fontSize: 13 },
  sectionHeader: { fontSize: 16, fontWeight: "700", color: "#0f172a", marginBottom: 4 },
  suggestionCard: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    gap: 12,
  },
  suggestionNumber: {
    backgroundColor: "#eff6ff",
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  suggestionNumberText: { fontSize: 13, fontWeight: "700", color: "#2563eb" },
  suggestionBody: { fontSize: 14, color: "#1e293b", lineHeight: 20 },
  charCount: { fontSize: 11, color: "#94a3b8", marginTop: 4 },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 24,
  },
  consentIconRow: { alignItems: "center", marginBottom: 12 },
  consentTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0f172a",
    textAlign: "center",
    marginBottom: 12,
  },
  consentBody: { fontSize: 14, color: "#334155", lineHeight: 20, marginBottom: 16 },
  consentCheckboxRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 20 },
  consentCheckboxLabel: { fontSize: 13, color: "#1e293b", fontWeight: "600", flex: 1 },
  modalButtons: { flexDirection: "row", justifyContent: "flex-end", gap: 12 },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#f1f5f9",
  },
  cancelButtonText: { color: "#475569", fontWeight: "600" },
  confirmConsentButton: {
    backgroundColor: "#2563eb",
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
  },
  confirmConsentText: { color: "#ffffff", fontWeight: "600" },
  disabledButton: { opacity: 0.5 },
});
