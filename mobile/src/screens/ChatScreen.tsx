import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { apiClient } from '@/services/api';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';
import type { ChatMessage, Chat } from '@/types';

interface ChatScreenProps {
  chatId?: string;
}

/**
 * Chat screen — private 1-on-1 conversation.
 * Shows list of messages and allows sending new ones.
 */
export function ChatScreen({ chatId }: ChatScreenProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChat, setSelectedChat] = useState<string | null>(chatId ?? null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  // Load list of chats
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const { data } = await apiClient.get('/chat/');
        setChats(data.chats);
      } catch {
        // Handle error gracefully
      }
    };
    fetchChats();
  }, []);

  // Load messages when a chat is selected
  useEffect(() => {
    if (!selectedChat) return;

    const fetchMessages = async () => {
      setLoading(true);
      try {
        const { data } = await apiClient.get(`/chat/${selectedChat}/messages`);
        setMessages(data);
      } catch {
        // Handle error gracefully
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
  }, [selectedChat]);

  const handleSend = async () => {
    if (!inputText.trim() || !selectedChat) return;

    try {
      const { data } = await apiClient.post(`/chat/${selectedChat}/messages`, {
        text: inputText.trim(),
      });
      setMessages((prev) => [...prev, data]);
      setInputText('');
    } catch {
      // Handle error gracefully
    }
  };

  // Show chat list if no chat selected
  if (!selectedChat) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Chats</Text>
        </View>

        {chats.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              No chats yet.{'\n'}React to someone's message to start a connection! ❤️
            </Text>
          </View>
        ) : (
          <FlatList
            data={chats}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.chatItem}
                onPress={() => setSelectedChat(item.id)}
              >
                <Text style={styles.chatItemTitle}>Anonymous</Text>
                <Text style={styles.chatItemPreview} numberOfLines={1}>
                  {item.last_message ?? 'No messages yet'}
                </Text>
              </TouchableOpacity>
            )}
          />
        )}
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={88}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => setSelectedChat(null)}>
          <Text style={styles.backBtn}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Anonymous</Text>
      </View>

      {/* Messages */}
      {loading ? (
        <ActivityIndicator color={COLORS.primary} style={styles.loader} />
      ) : (
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View
              style={[
                styles.messageBubble,
                item.is_mine ? styles.messageMine : styles.messageTheirs,
              ]}
            >
              <Text style={[styles.messageText, item.is_mine && styles.messageTextMine]}>
                {item.text}
              </Text>
            </View>
          )}
          contentContainerStyle={styles.messageList}
          inverted
        />
      )}

      {/* Input */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Message..."
          placeholderTextColor={COLORS.textMuted}
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxLength={1000}
        />
        <TouchableOpacity
          style={[styles.sendBtn, !inputText.trim() && styles.sendBtnDisabled]}
          onPress={handleSend}
          disabled={!inputText.trim()}
        >
          <Text style={styles.sendBtnText}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 56,
    paddingBottom: 12,
    borderBottomColor: COLORS.border,
    borderBottomWidth: 1,
    gap: 12,
  },
  backBtn: {
    color: COLORS.primary,
    fontSize: 24,
  },
  title: {
    ...TYPOGRAPHY.h2,
    color: COLORS.text,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textMuted,
    textAlign: 'center',
    lineHeight: 24,
  },
  loader: {
    flex: 1,
  },
  chatItem: {
    padding: 16,
    borderBottomColor: COLORS.border,
    borderBottomWidth: 1,
  },
  chatItemTitle: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    fontWeight: '600',
    marginBottom: 4,
  },
  chatItemPreview: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
  },
  messageList: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    flexGrow: 1,
  },
  messageBubble: {
    maxWidth: '75%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginVertical: 4,
  },
  messageMine: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.primary,
    borderBottomRightRadius: 4,
  },
  messageTheirs: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.surface,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    color: COLORS.text,
    fontSize: 15,
    lineHeight: 20,
  },
  messageTextMine: {
    color: COLORS.background,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderTopColor: COLORS.border,
    borderTopWidth: 1,
    backgroundColor: COLORS.surface,
  },
  input: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: COLORS.text,
    fontSize: 15,
    maxHeight: 100,
    borderColor: COLORS.border,
    borderWidth: 1,
    marginRight: 8,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendBtnText: {
    color: COLORS.background,
    fontSize: 18,
    fontWeight: '700',
  },
});
