import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from 'react-native';
import { UserCounter } from '@/components/UserCounter';
import { MessageItem } from '@/components/MessageItem';
import { MessageSkeleton } from '@/components/MessageSkeleton';
import { useMessages } from '@/hooks/useMessages';
import { useLocation } from '@/hooks/useLocation';
import { useMessagesStore } from '@/store/messagesStore';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';

// Minimum time to show the shimmer skeleton (improves perceived experience)
const MIN_SKELETON_MS = 1500;

/**
 * Room screen — main screen showing nearby anonymous messages.
 * Users can see how many people are nearby, read and post messages,
 * and react with likes.
 */
export function RoomScreen() {
  const [inputText, setInputText] = useState('');
  const { location } = useLocation();
  const { messages, loading, sendMessage, refresh } = useMessages();
  const nearbyCount = useMessagesStore((state) => state.nearbyCount);

  // Show skeleton for at least MIN_SKELETON_MS on first load
  const [showSkeleton, setShowSkeleton] = useState(true);
  const skeletonTimerRef = useRef<number | null>(null);

  useEffect(() => {
    skeletonTimerRef.current = setTimeout(() => {
      setShowSkeleton(false);
    }, MIN_SKELETON_MS) as unknown as number;
    return () => {
      if (skeletonTimerRef.current) clearTimeout(skeletonTimerRef.current);
    };
  }, []);

  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || !location) return;

    await sendMessage(text);
    setInputText('');
  }, [inputText, location, sendMessage]);

  const isInitialLoad = showSkeleton && messages.length === 0;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={88}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.roomTitle}>Room</Text>
        <UserCounter count={nearbyCount} />
      </View>

      {/* Skeleton loading state */}
      {isInitialLoad ? (
        <MessageSkeleton />
      ) : (
        /* Messages list */
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <MessageItem message={item} />}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={refresh}
              tintColor={COLORS.primary}
            />
          }
          inverted
        />
      )}

      {/* Input bar */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Say something anonymously..."
          placeholderTextColor={COLORS.textMuted}
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxLength={500}
          returnKeyType="send"
          onSubmitEditing={handleSend}
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
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 56,
    paddingBottom: 12,
    borderBottomColor: COLORS.border,
    borderBottomWidth: 1,
  },
  roomTitle: {
    ...TYPOGRAPHY.h2,
    color: COLORS.text,
    letterSpacing: 4,
  },
  list: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    flexGrow: 1,
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
