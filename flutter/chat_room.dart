import 'package:flutter/material.dart';
import 'chat_message_bubble.dart';
import 'chat_service.dart';

class ChatRoom extends StatefulWidget {
  const ChatRoom({super.key});

  @override
  State<ChatRoom> createState() => _ChatRoomState();
}

class _ChatRoomState extends State<ChatRoom> {
  final TextEditingController _controller = TextEditingController();
  final ChatService _service = ChatService();
  final List<ChatMessage> _messages = [];
  int? _sessionId;

  Future<void> _send() async {
    final text = _controller.text;
    if (text.isEmpty) return;
    setState(() {
      _messages.add(ChatMessage(text: text, isMe: true));
    });
    _controller.clear();

    _sessionId ??= await _service.createSession();
    final reply = await _service.sendMessage(_sessionId!, text);
    setState(() {
      _messages.add(ChatMessage(text: reply ?? 'error', isMe: false));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat Room')),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              children: _messages
                  .map((m) => ChatMessageBubble(message: m))
                  .toList(),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(controller: _controller),
                ),
                IconButton(onPressed: _send, icon: const Icon(Icons.send))
              ],
            ),
          ),
        ],
      ),
    );
  }
}
