import 'package:flutter/material.dart';

class ChatSession {
  final int sessionId;
  final DateTime createdAt;
  final bool isActive;
  
  ChatSession({
    required this.sessionId,
    required this.createdAt,
    this.isActive = true,
  });

  factory ChatSession.fromJson(Map<String, dynamic> json) {
    return ChatSession(
      sessionId: json['session_id'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

enum MessageType { text, image, system }

class ChatMessage {
  final String id;
  final String text;
  final String sender;
  final DateTime timestamp;
  final MessageType type;
  final String? imagePath;
  final String? imageBase64;
  final String? replyTo;
  final Map<String, dynamic>? extra;

  ChatMessage({
    required this.id,
    required this.text,
    required this.sender,
    required this.timestamp,
    this.type = MessageType.text,
    this.imagePath,
    this.imageBase64,
    this.replyTo,
    this.extra,
  });

  factory ChatMessage.user(String text, {String? replyTo, MessageType type = MessageType.text, String? imagePath, String? imageBase64}) {
    return ChatMessage(
      id: DateTime.now().toIso8601String(),
      text: text,
      sender: 'user',
      timestamp: DateTime.now(),
      type: type,
      replyTo: replyTo,
      imagePath: imagePath,
      imageBase64: imageBase64,
    );
  }

  factory ChatMessage.bot(String text, {Map<String, dynamic>? extra}) {
    return ChatMessage(
      id: DateTime.now().toIso8601String(),
      text: text,
      sender: 'bot',
      timestamp: DateTime.now(),
      extra: extra,
    );
  }

  factory ChatMessage.system(String text) {
    return ChatMessage(
      id: DateTime.now().toIso8601String(),
      text: text,
      sender: 'system',
      timestamp: DateTime.now(),
      type: MessageType.system,
    );
  }

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String,
      text: json['text'] as String,
      sender: json['sender'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      type: _typeFromString(json['message_type'] as String?),
      imagePath: json['image_path'] as String?,
      imageBase64: json['image_base64'] as String?,
      replyTo: json['replyTo'] as String?,
      extra: json['extra'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'sender': sender,
      'timestamp': timestamp.toIso8601String(),
      'message_type': type.name,
      'image_path': imagePath,
      'image_base64': imageBase64,
      'replyTo': replyTo,
      'extra': extra,
    };
  }

  static MessageType _typeFromString(String? type) {
    switch (type) {
      case 'image': return MessageType.image;
      case 'system': return MessageType.system;
      default: return MessageType.text;
    }
  }
}
