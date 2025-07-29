import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_staggered_animations/flutter_staggered_animations.dart';
import 'package:intl/intl.dart';

class ChatColors {
  static const primaryGreen = Color(0xFF2E7D66);
  static const lightGreen = Color(0xFF4CAF50);
  static const darkGreen = Color(0xFF1B5E20);
  static const paleGreen = Color(0xFFE8F7E8);
  static const softGreen = Color(0xFF66BB6A);
  static const backgroundGreen = Color(0xFFF1F8E9);
}

class TypewriterText extends StatefulWidget {
  final String text;
  final Duration duration;
  final TextStyle? style;
  final bool shouldAnimate;

  const TypewriterText({
    super.key,
    required this.text,
    this.duration = const Duration(milliseconds: 50),
    this.style,
    this.shouldAnimate = true,
  });

  @override
  State<TypewriterText> createState() => _TypewriterTextState();
}

class _TypewriterTextState extends State<TypewriterText>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<int> _animation;
  String displayText = '';

  @override
  void initState() {
    super.initState();
    
    if (!widget.shouldAnimate) {
      displayText = widget.text;
      _controller = AnimationController(
        duration: const Duration(milliseconds: 1),
        vsync: this,
      );
      return;
    }

    _controller = AnimationController(
      duration: Duration(milliseconds: widget.text.length * widget.duration.inMilliseconds),
      vsync: this,
    );

    _animation = IntTween(
      begin: 0,
      end: widget.text.length,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _animation.addListener(() {
      if (mounted) {
        setState(() {
          displayText = widget.text.substring(0, _animation.value);
        });
      }
    });

    _controller.forward();
  }

  @override
  void didUpdateWidget(TypewriterText oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    if (oldWidget.text != widget.text && widget.shouldAnimate) {
      _controller.reset();
      displayText = '';
      
      _animation = IntTween(
        begin: 0,
        end: widget.text.length,
      ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));
      
      _controller.forward();
    } else if (!widget.shouldAnimate) {
      displayText = widget.text;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SelectableText(
      displayText,
      style: widget.style,
      textDirection: Directionality.of(context),
    );
  }
}

class ChatMessageBubble extends StatelessWidget {
  final Map<String, dynamic> msg;
  final int index;
  final VoidCallback onDelete;
  final VoidCallback onReply;
  final VoidCallback onShare;
  final VoidCallback onCopy;
  final Set<String> animatedMessages;
  final Set<String> selectedMessages;
  final bool selectionMode;
  final Function(String) onToggleSelection;

  const ChatMessageBubble({
    super.key,
    required this.msg,
    required this.index,
    required this.onDelete,
    required this.onReply,
    required this.onShare,
    required this.onCopy,
    required this.animatedMessages,
    required this.selectedMessages,
    required this.selectionMode,
    required this.onToggleSelection,
  });

  String _formatTime(DateTime ts) => DateFormat('HH:mm').format(ts);

  void _showContextMenu(BuildContext context, TapDownDetails details) {
    final RenderBox overlay = Overlay.of(context).context.findRenderObject() as RenderBox;
    final RelativeRect position = RelativeRect.fromRect(
      Rect.fromPoints(details.globalPosition, details.globalPosition),
      Offset.zero & overlay.size,
    );

    showMenu(
      context: context,
      position: position,
      color: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 8,
      items: [
        PopupMenuItem(
          value: 'reply',
          child: Row(
            children: [
              Icon(Icons.reply, color: ChatColors.primaryGreen, size: 20),
              const SizedBox(width: 12),
              const Text('پاسخ'),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'copy',
          child: Row(
            children: [
              Icon(Icons.copy, color: ChatColors.primaryGreen, size: 20),
              const SizedBox(width: 12),
              const Text('کپی'),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'share',
          child: Row(
            children: [
              Icon(Icons.share, color: ChatColors.primaryGreen, size: 20),
              const SizedBox(width: 12),
              const Text('اشتراک‌گذاری'),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'delete',
          child: Row(
            children: [
              Icon(Icons.delete, color: Colors.red.shade600, size: 20),
              const SizedBox(width: 12),
              Text('حذف', style: TextStyle(color: Colors.red.shade600)),
            ],
          ),
        ),
      ],
    ).then((value) {
      switch (value) {
        case 'reply':
          onReply();
          break;
        case 'copy':
          onCopy();
          break;
        case 'share':
          onShare();
          break;
        case 'delete':
          onDelete();
          break;
      }
    });
  }

  Widget _buildImagePreview(BuildContext context) {
    final double maxWidth = MediaQuery.of(context).size.width * 0.6;
    final String? localPath = msg['image_path'];
    final String? base64Image = msg['image_base64'];

    Widget imageWidget;

    if (localPath != null && !kIsWeb && File(localPath).existsSync()) {
      imageWidget = Image.file(
        File(localPath),
        width: maxWidth,
        height: 160,
        fit: BoxFit.cover,
      );
    } else if (base64Image != null) {
      try {
        final bytes = base64Decode(base64Image);
        imageWidget = Image.memory(
          Uint8List.fromList(bytes),
          width: maxWidth,
          height: 160,
          fit: BoxFit.cover,
        );
      } catch (e) {
        imageWidget = _buildImageFallback();
      }
    } else {
      imageWidget = _buildImageFallback();
    }

    return Container(
      constraints: BoxConstraints(maxWidth: maxWidth),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: ChatColors.lightGreen.withOpacity(0.3)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: imageWidget,
            ),
          ),
          if (msg['text'] != null && msg['text'].toString().isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: ChatColors.paleGreen.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.image, size: 16, color: ChatColors.primaryGreen),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      msg['text'],
                      style: const TextStyle(
                        fontSize: 14,
                        color: ChatColors.darkGreen,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildImageFallback() {
    return Container(
      width: 200,
      height: 160,
      decoration: BoxDecoration(
        color: ChatColors.paleGreen,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ChatColors.lightGreen.withOpacity(0.5)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.image,
            size: 48,
            color: ChatColors.primaryGreen.withOpacity(0.7),
          ),
          const SizedBox(height: 8),
          Text(
            'تصویر پزشکی',
            style: TextStyle(
              color: ChatColors.darkGreen,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageContent(BuildContext context) {
    final isUser = msg['sender'] == 'user';
    final messageType = msg['message_type'] ?? 'text';
    final isTyping = msg['isTyping'] == true;
    final hasBeenAnimated = animatedMessages.contains(msg['id']?.toString() ?? '');

    // System message
    if (messageType == 'system') {
      return Container(
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 32),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: ChatColors.paleGreen.withOpacity(0.5),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: ChatColors.lightGreen.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Icon(Icons.info_outline, color: ChatColors.primaryGreen, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                msg['text'] ?? '',
                style: TextStyle(
                  color: ChatColors.darkGreen,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      );
    }

    // Image message
    if (messageType == 'image') {
      return _buildImagePreview(context);
    }

    // Text message
    if (isUser || !isTyping) {
      return SelectableText(
        msg['text'] ?? '',
        style: TextStyle(
          color: isUser ? Colors.white : ChatColors.darkGreen,
          fontSize: 16,
          height: 1.45,
          fontFamily: 'Vazirmatn',
        ),
        textDirection: Directionality.of(context),
      );
    } else {
      return TypewriterText(
        text: msg['text'] ?? '',
        duration: const Duration(milliseconds: 30),
        shouldAnimate: !hasBeenAnimated,
        style: TextStyle(
          color: ChatColors.darkGreen,
          fontSize: 16,
          height: 1.45,
          fontFamily: 'Vazirmatn',
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isUser = msg['sender'] == 'user';
    final messageId = msg['id']?.toString() ?? '';
    final isSelected = selectedMessages.contains(messageId);
    final messageType = msg['message_type'] ?? 'text';
    
    // System messages
    if (messageType == 'system') {
      return AnimationConfiguration.staggeredList(
        position: index,
        duration: const Duration(milliseconds: 240),
        child: SlideAnimation(
          verticalOffset: 32,
          child: FadeInAnimation(
            child: _buildMessageContent(context),
          ),
        ),
      );
    }
    
    final borderRadius = BorderRadius.only(
      topLeft: const Radius.circular(18),
      topRight: const Radius.circular(18),
      bottomLeft: isUser ? const Radius.circular(18) : const Radius.circular(4),
      bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(18),
    );

    final BoxDecoration botGlassDecoration = BoxDecoration(
      color: Colors.white.withOpacity(0.9),
      borderRadius: borderRadius,
      boxShadow: [
        BoxShadow(
          color: ChatColors.primaryGreen.withOpacity(0.1),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
      ],
      border: Border.all(
        color: isSelected 
            ? ChatColors.primaryGreen 
            : ChatColors.lightGreen.withOpacity(0.3),
        width: isSelected ? 2 : 1,
      ),
    );

    return AnimationConfiguration.staggeredList(
      position: index,
      duration: const Duration(milliseconds: 240),
      child: SlideAnimation(
        verticalOffset: 32,
        child: FadeInAnimation(
          child: Align(
            alignment: isUser
                ? AlignmentDirectional.centerEnd
                : AlignmentDirectional.centerStart,
            child: Padding(
              padding: EdgeInsetsDirectional.only(
                end: isUser ? 6 : 60,
                start: isUser ? (selectionMode ? 50 : 60) : 6,
                top: 2,
                bottom: 2,
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (selectionMode && isUser)
                    Container(
                      margin: const EdgeInsets.only(left: 8, bottom: 8),
                      child: InkWell(
                        onTap: () => onToggleSelection(messageId),
                        borderRadius: BorderRadius.circular(20),
                        child: Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: isSelected 
                                  ? ChatColors.primaryGreen 
                                  : Colors.grey.shade400,
                              width: 2,
                            ),
                            color: isSelected ? ChatColors.primaryGreen : Colors.transparent,
                          ),
                          child: isSelected
                              ? const Icon(Icons.check, color: Colors.white, size: 16)
                              : null,
                        ),
                      ),
                    ),
                  
                  Flexible(
                    child: GestureDetector(
                      onTap: selectionMode 
                          ? () => onToggleSelection(messageId)
                          : () {
                              final time = _formatTime(DateTime.parse(msg['timestamp']));
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('ارسال‌شده در $time'),
                                  duration: const Duration(milliseconds: 1200),
                                  backgroundColor: Colors.black87,
                                  behavior: SnackBarBehavior.floating,
                                  margin: const EdgeInsets.symmetric(horizontal: 80, vertical: 12),
                                ),
                              );
                            },
                      onTapDown: !selectionMode ? (details) => _showContextMenu(context, details) : null,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        curve: Curves.easeOut,
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.75,
                        ),
                        padding: EdgeInsets.symmetric(
                          horizontal: 14, 
                          vertical: messageType == 'image' ? 10 : 12
                        ),
                        decoration: isUser
                            ? BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [ChatColors.primaryGreen, ChatColors.darkGreen],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: borderRadius,
                                border: isSelected ? Border.all(color: Colors.white, width: 2) : null,
                                boxShadow: [
                                  BoxShadow(
                                    color: ChatColors.primaryGreen.withOpacity(0.3),
                                    blurRadius: 7,
                                    offset: const Offset(0, 2),
                                  ),
                                ],
                              )
                            : botGlassDecoration,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildMessageContent(context),
                            const SizedBox(height: 6),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              textDirection: Directionality.of(context),
                              children: [
                                Text(
                                  _formatTime(DateTime.parse(msg['timestamp'])),
                                  style: TextStyle(
                                    color: isUser 
                                        ? Colors.white70 
                                        : ChatColors.primaryGreen.withOpacity(0.7),
                                    fontSize: 11,
                                  ),
                                ),
                                if (isUser) ...[
                                  const SizedBox(width: 4),
                                  Icon(Icons.done_all, size: 14, color: Colors.white70),
                                ],
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  
                  if (selectionMode && !isUser)
                    Container(
                      margin: const EdgeInsets.only(right: 8, bottom: 8),
                      child: InkWell(
                        onTap: () => onToggleSelection(messageId),
                        borderRadius: BorderRadius.circular(20),
                        child: Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: isSelected 
                                  ? ChatColors.primaryGreen 
                                  : Colors.grey.shade400,
                              width: 2,
                            ),
                            color: isSelected ? ChatColors.primaryGreen : Colors.transparent,
                          ),
                          child: isSelected
                              ? const Icon(Icons.check, color: Colors.white, size: 16)
                              : null,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
