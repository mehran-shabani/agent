import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class ChatColors {
  static const primaryGreen = Color(0xFF2E7D66);
  static const lightGreen = Color(0xFF4CAF50);
  static const darkGreen = Color(0xFF1B5E20);
  static const paleGreen = Color(0xFFE8F7E8);
  static const softGreen = Color(0xFF66BB6A);
  static const backgroundGreen = Color(0xFFF1F8E9);
}

class ChatInputArea extends StatefulWidget {
  final TextEditingController messageController;
  final FocusNode focusNode;
  final VoidCallback onSend;
  final VoidCallback onPickImage;

  const ChatInputArea({
    super.key,
    required this.messageController,
    required this.focusNode,
    required this.onSend,
    required this.onPickImage,
  });

  @override
  State<ChatInputArea> createState() => _ChatInputAreaState();
}

class _ChatInputAreaState extends State<ChatInputArea> with TickerProviderStateMixin {
  bool _showEmojiPicker = false;
  bool _isExpanded = false;
  late AnimationController _expandController;
  late Animation<double> _expandAnimation;

  final List<String> _popularEmojis = [
    '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃',
    '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙',
    '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔',
    '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥',
    '😔', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢',
    '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱',
    '👍', '👎', '👏', '🙌', '👐', '🤲', '🤝', '🙏', '✌️', '🤞',
    '💪', '🦾', '🖤', '🤍', '🤎', '💜', '💙', '💚', '💛', '🧡',
    '❤️', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝'
  ];

  @override
  void initState() {
    super.initState();
    widget.messageController.addListener(_onInputChanged);
    _expandController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _expandController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    widget.messageController.removeListener(_onInputChanged);
    _expandController.dispose();
    super.dispose();
  }

  bool get hasText => widget.messageController.text.trim().isNotEmpty;

  void _onInputChanged() => setState(() {});

  void _toggleExpansion() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _expandController.forward();
        widget.focusNode.requestFocus();
      } else {
        _expandController.reverse();
        widget.focusNode.unfocus();
        _showEmojiPicker = false;
      }
    });
  }

  void _toggleEmojiPicker() {
    setState(() => _showEmojiPicker = !_showEmojiPicker);
    if (!_showEmojiPicker) {
      FocusScope.of(context).requestFocus(widget.focusNode);
    } else {
      widget.focusNode.unfocus();
    }
  }

  void _insertEmoji(String emoji) {
    final text = widget.messageController.text;
    final selection = widget.messageController.selection;
    final newText = text.replaceRange(selection.start, selection.end, emoji);
    widget.messageController.value = widget.messageController.value.copyWith(
      text: newText,
      selection: TextSelection.collapsed(offset: selection.start + emoji.length),
    );
  }

  void _handleSend() {
    if (!hasText) return;
    widget.onSend();
    HapticFeedback.lightImpact();
    setState(() {
      _showEmojiPicker = false;
      _isExpanded = false;
    });
    _expandController.reverse();
  }

  void _handlePaste() async {
    final data = await Clipboard.getData('text/plain');
    if (data?.text != null) {
      final text = data!.text!;
      final selection = widget.messageController.selection;
      final newText = widget.messageController.text.replaceRange(
        selection.start, selection.end, text,
      );
      widget.messageController.value = widget.messageController.value.copyWith(
        text: newText,
        selection: TextSelection.collapsed(offset: selection.start + text.length),
      );
    }
  }

  Widget _buildEmojiPicker() {
    return Container(
      height: 250,
      margin: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: ChatColors.lightGreen.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: ChatColors.primaryGreen.withOpacity(0.08),
            blurRadius: 16,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: ChatColors.paleGreen,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
            ),
            child: Row(
              children: [
                Text(
                  'ایموجی‌ها',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: ChatColors.darkGreen,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: Icon(Icons.close, color: ChatColors.primaryGreen),
                  onPressed: () => setState(() => _showEmojiPicker = false),
                ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 8,
                  childAspectRatio: 1,
                ),
                itemCount: _popularEmojis.length,
                itemBuilder: (context, index) {
                  final emoji = _popularEmojis[index];
                  return Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(8),
                      onTap: () => _insertEmoji(emoji),
                      child: Container(
                        alignment: Alignment.center,
                        child: Text(
                          emoji,
                          style: const TextStyle(fontSize: 24),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExpandedActions() {
    return AnimatedBuilder(
      animation: _expandAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _expandAnimation.value,
          child: Opacity(
            opacity: _expandAnimation.value,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: Icon(
                    Icons.emoji_emotions_outlined,
                    color: _showEmojiPicker ? ChatColors.darkGreen : ChatColors.primaryGreen,
                    size: 26,
                  ),
                  splashRadius: 22,
                  tooltip: 'ایموجی',
                  onPressed: _toggleEmojiPicker,
                ),
                IconButton(
                  icon: Icon(
                    Icons.image,
                    color: ChatColors.primaryGreen,
                    size: 24,
                  ),
                  splashRadius: 22,
                  tooltip: 'ارسال تصویر پزشکی',
                  onPressed: widget.onPickImage,
                ),
                IconButton(
                  icon: Icon(
                    Icons.content_paste_go,
                    size: 23,
                    color: ChatColors.primaryGreen,
                  ),
                  splashRadius: 22,
                  tooltip: 'چسباندن',
                  onPressed: _handlePaste,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_showEmojiPicker) _buildEmojiPicker(),
          
          Container(
            margin: const EdgeInsets.fromLTRB(12, 10, 12, 16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (!_isExpanded)
                  Container(
                    margin: const EdgeInsets.only(left: 8),
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(
                            Icons.emoji_emotions_outlined,
                            color: ChatColors.primaryGreen,
                            size: 28,
                          ),
                          splashRadius: 24,
                          tooltip: 'ایموجی',
                          onPressed: _toggleEmojiPicker,
                        ),
                        IconButton(
                          icon: Icon(
                            Icons.image,
                            color: ChatColors.primaryGreen,
                            size: 26,
                          ),
                          splashRadius: 24,
                          tooltip: 'ارسال تصویر پزشکی',
                          onPressed: widget.onPickImage,
                        ),
                      ],
                    ),
                  ),
                
                Expanded(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    curve: Curves.easeInOut,
                    padding: EdgeInsets.symmetric(
                      vertical: 6,
                      horizontal: _isExpanded ? 10 : 16,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(_isExpanded ? 26 : 25),
                      border: Border.all(
                        color: _isExpanded 
                            ? ChatColors.primaryGreen.withOpacity(0.5)
                            : ChatColors.lightGreen.withOpacity(0.3),
                        width: _isExpanded ? 2 : 1,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: ChatColors.primaryGreen.withOpacity(_isExpanded ? 0.15 : 0.08),
                          blurRadius: _isExpanded ? 20 : 16,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        if (_isExpanded) _buildExpandedActions(),
                        
                        Expanded(
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxHeight: 120),
                            child: TextField(
                              controller: widget.messageController,
                              focusNode: widget.focusNode,
                              textInputAction: TextInputAction.send,
                              minLines: 1,
                              maxLines: 4,
                              decoration: InputDecoration(
                                border: InputBorder.none,
                                hintText: _isExpanded 
                                    ? 'پیام خود را بنویسید…'
                                    : 'پیام...',
                                hintStyle: TextStyle(
                                  color: ChatColors.primaryGreen.withOpacity(0.5),
                                  fontSize: _isExpanded ? 16 : 14,
                                ),
                                contentPadding: const EdgeInsets.symmetric(
                                  vertical: 10,
                                  horizontal: 8,
                                ),
                              ),
                              style: TextStyle(
                                fontSize: 16,
                                color: ChatColors.darkGreen,
                              ),
                              textDirection: TextDirection.rtl,
                              onSubmitted: (_) => _handleSend(),
                              onTap: () {
                                if (!_isExpanded) {
                                  _toggleExpansion();
                                }
                                setState(() => _showEmojiPicker = false);
                              },
                              enableSuggestions: true,
                              autocorrect: true,
                            ),
                          ),
                        ),
                        
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 200),
                          transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
                          child: hasText
                              ? Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    onTap: _handleSend,
                                    borderRadius: BorderRadius.circular(22),
                                    child: Container(
                                      decoration: BoxDecoration(
                                        gradient: LinearGradient(
                                          colors: [ChatColors.primaryGreen, ChatColors.darkGreen],
                                        ),
                                        borderRadius: BorderRadius.circular(22),
                                        boxShadow: [
                                          BoxShadow(
                                            color: ChatColors.primaryGreen.withOpacity(0.3),
                                            blurRadius: 6,
                                            offset: const Offset(0, 1),
                                          ),
                                        ],
                                      ),
                                      padding: const EdgeInsets.all(12),
                                      child: const Icon(
                                        Icons.send_rounded,
                                        color: Colors.white,
                                        size: 22,
                                      ),
                                    ),
                                  ),
                                )
                              : Container(
                                  padding: const EdgeInsets.all(12),
                                  child: Icon(
                                    Icons.send_rounded,
                                    color: Colors.grey.shade300,
                                    size: 22,
                                  ),
                                ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
