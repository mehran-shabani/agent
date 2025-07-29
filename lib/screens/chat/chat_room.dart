import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:animated_text_kit/animated_text_kit.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

import '../services/chat_service.dart';
import '../services/chat_models.dart';
import '../widgets/chat_message_bubble.dart';
import '../widgets/chat_input_area.dart';
import '../utils/snackbar.dart';

class ChatColors {
  static const primaryGreen = Color(0xFF2E7D66);
  static const lightGreen = Color(0xFF4CAF50);
  static const darkGreen = Color(0xFF1B5E20);
  static const paleGreen = Color(0xFFE8F7E8);
  static const softGreen = Color(0xFF66BB6A);
  static const backgroundGreen = Color(0xFFF1F8E9);
}

class GradientTween extends Tween<Gradient> {
  GradientTween({required Gradient begin, required Gradient end})
      : super(begin: begin, end: end);

  @override
  Gradient lerp(double t) {
    if (begin is LinearGradient && end is LinearGradient) {
      final LinearGradient b = begin as LinearGradient;
      final LinearGradient e = end as LinearGradient;
      return LinearGradient(
        begin: Alignment.lerp(b.begin as Alignment?, e.begin as Alignment?, t)!,
        end: Alignment.lerp(b.end as Alignment?, e.end as Alignment?, t)!,
        colors: List.generate(
          b.colors.length,
          (i) => Color.lerp(b.colors[i], e.colors[i], t)!,
        ),
        stops: b.stops ?? e.stops,
      );
    }
    return t < 0.5 ? begin! : end!;
  }
}

class AnimatedTitle extends StatefulWidget {
  const AnimatedTitle({super.key});

  @override
  State<AnimatedTitle> createState() => _AnimatedTitleState();
}

class _AnimatedTitleState extends State<AnimatedTitle>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Gradient> _gradientAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );

    _gradientAnimation = GradientTween(
      begin: LinearGradient(
        colors: [ChatColors.lightGreen, Colors.white],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      end: LinearGradient(
        colors: [Colors.white, ChatColors.softGreen],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTap() {
    if (_controller.status != AnimationStatus.forward) {
      _controller.forward().then((_) {
        _controller.reverse();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _handleTap,
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: ChatColors.paleGreen,
            radius: 18,
            child: Icon(Icons.auto_awesome, color: ChatColors.darkGreen, size: 20),
          ),
          const SizedBox(width: 8),
          AnimatedBuilder(
            animation: _gradientAnimation,
            builder: (context, child) {
              return ShaderMask(
                shaderCallback: (bounds) {
                  return _gradientAnimation.value.createShader(
                    Rect.fromLTWH(0, 0, bounds.width, bounds.height),
                  );
                },
                child: child,
              );
            },
            child: const Text(
              'DocAI Assistant',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class AnimatedBackground extends StatefulWidget {
  const AnimatedBackground({super.key});
  @override
  State<AnimatedBackground> createState() => _AnimatedBackgroundState();
}

class _AnimatedBackgroundState extends State<AnimatedBackground> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<Particle> _particles = [];
  final Random _random = Random();
  Size? _screenSize;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(seconds: 20),)..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _initializeParticles(Size size) {
    if (size == _screenSize) return;
    _screenSize = size;
    _particles.clear();
    int particleCount = 30;
    for (int i = 0; i < particleCount; i++) {
      _particles.add(_createParticle(size));
    }
  }

  Particle _createParticle(Size size) {
    return Particle(
      position: Offset(_random.nextDouble() * size.width, _random.nextDouble() * size.height),
      color: ChatColors.lightGreen.withOpacity(_random.nextDouble() * 0.1 + 0.05),
      radius: _random.nextDouble() * 20 + 10,
      velocity: Offset((_random.nextDouble() - 0.5) * 0.4, (_random.nextDouble() - 0.5) * 0.4),
    );
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final size = Size(constraints.maxWidth, constraints.maxHeight);
        _initializeParticles(size);
        return AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return CustomPaint(painter: BackgroundPainter(_particles, _random), child: Container());
          },
        );
      },
    );
  }
}

class Particle {
  Offset position;
  Color color;
  double radius;
  Offset velocity;
  Particle({required this.position, required this.color, required this.radius, required this.velocity});
}

class BackgroundPainter extends CustomPainter {
  final List<Particle> particles;
  final Random random;
  BackgroundPainter(this.particles, this.random);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    if (particles.isEmpty) return;
    for (var particle in particles) {
      particle.position += particle.velocity;
      if (particle.position.dx < -particle.radius) {
        particle.position = Offset(size.width + particle.radius, random.nextDouble() * size.height);
      } else if (particle.position.dx > size.width + particle.radius) {
        particle.position = Offset(-particle.radius, random.nextDouble() * size.height);
      }
      if (particle.position.dy < -particle.radius) {
        particle.position = Offset(random.nextDouble() * size.width, size.height + particle.radius);
      } else if (particle.position.dy > size.height + particle.radius) {
        particle.position = Offset(random.nextDouble() * size.width, -particle.radius);
      }
      paint.color = particle.color;
      canvas.drawCircle(particle.position, particle.radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class ChatRoom extends StatefulWidget {
  const ChatRoom({super.key});

  @override
  State<ChatRoom> createState() => _ChatRoomState();
}

class _ChatRoomState extends State<ChatRoom> with TickerProviderStateMixin, WidgetsBindingObserver {
  static const double _kAppBarHeight = 56;
  static const Duration _sessionTimeoutDuration = Duration(seconds: 10);
  
  final ChatService _chatService = ChatService();
  final ImagePicker _imagePicker = ImagePicker();
  
  final TextEditingController messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();
  
  final Set<String> _animatedMessages = <String>{};
  final Set<String> _selectedMessages = <String>{};
  
  List<Map<String, dynamic>> currentMessages = [];
  int? currentSessionId;
  
  bool isTyping = false;
  bool _showScrollButton = false;
  bool _selectionMode = false;
  String? _replyingToMessage;
  
  Timer? _sessionTimeoutTimer;
  Timer? _warningTimer;
  bool _showTimeoutWarning = false;
  int _timeoutCountdown = 10;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeChat();
    _setupScrollController();
    _startSessionTimeout();
  }
  
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _sessionTimeoutTimer?.cancel();
    _warningTimer?.cancel();
    if (currentSessionId != null) {
      _chatService.endSession(currentSessionId!);
    }
    _scrollController.dispose();
    messageController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    if (state == AppLifecycleState.resumed) {
      _startSessionTimeout();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      _pauseSessionTimeout();
    }
  }

  void _startSessionTimeout() {
    _resetSessionTimeout();
  }

  void _resetSessionTimeout() {
    _sessionTimeoutTimer?.cancel();
    _warningTimer?.cancel();
    setState(() => _showTimeoutWarning = false);
    
    if (currentSessionId != null) {
      _sessionTimeoutTimer = Timer(_sessionTimeoutDuration, () {
        _showSessionTimeoutWarning();
      });
    }
  }

  void _pauseSessionTimeout() {
    _sessionTimeoutTimer?.cancel();
    _warningTimer?.cancel();
  }

  void _showSessionTimeoutWarning() {
    if (!mounted) return;
    
    setState(() {
      _showTimeoutWarning = true;
      _timeoutCountdown = 10;
    });

    _warningTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      
      setState(() => _timeoutCountdown--);
      
      if (_timeoutCountdown <= 0) {
        timer.cancel();
        _autoCloseSession();
      }
    });
  }

  Future<void> _autoCloseSession() async {
    if (currentSessionId != null) {
      try {
        await _chatService.endSession(currentSessionId!);
        setState(() {
          currentSessionId = null;
          currentMessages.clear();
          _showTimeoutWarning = false;
        });
        CustomSnackBar.show('جلسه به علت عدم فعالیت بسته شد', context, isError: true);
        _initializeChat();
      } catch (e) {
        // Handle error
      }
    }
  }

  void _dismissTimeoutWarning() {
    _warningTimer?.cancel();
    setState(() => _showTimeoutWarning = false);
    _resetSessionTimeout();
  }

  void _initializeChat() async {
    try {
      // فرض بر این است که patient_id = 1 (باید از authentication گرفته شود)
      final sessionId = await _chatService.createSession(1);
      setState(() {
        currentSessionId = sessionId;
        currentMessages = [
          {
            'id': DateTime.now().toIso8601String(),
            'text': 'سلام! من دستیار پزشکی شما هستم. چطور می‌توانم کمکتان کنم؟',
            'sender': 'bot',
            'timestamp': DateTime.now().toIso8601String(),
            'message_type': 'system',
          }
        ];
      });
      _startSessionTimeout();
    } catch (e) {
      CustomSnackBar.show('خطا در ایجاد جلسه: $e', context, isError: true);
    }
  }

  void _setupScrollController() {
    _scrollController.addListener(() {
      setState(() => _showScrollButton = _scrollController.offset >= 400);
    });
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _toggleSelectionMode() {
    setState(() {
      _selectionMode = !_selectionMode;
      if (!_selectionMode) {
        _selectedMessages.clear();
      }
    });
  }

  void _toggleMessageSelection(String messageId) {
    setState(() {
      if (_selectedMessages.contains(messageId)) {
        _selectedMessages.remove(messageId);
      } else {
        _selectedMessages.add(messageId);
      }
      
      if (_selectedMessages.isEmpty) {
        _selectionMode = false;
      }
    });
  }

  void _deleteMessage(String messageId) {
    setState(() {
      currentMessages.removeWhere((msg) => msg['id'] == messageId);
      _animatedMessages.remove(messageId);
      _selectedMessages.remove(messageId);
    });
    CustomSnackBar.show('پیام حذف شد', context);
  }

  void _copyMessage(String messageText) {
    Clipboard.setData(ClipboardData(text: messageText));
    CustomSnackBar.show('پیام کپی شد', context);
  }

  void _shareMessage(String messageText) {
    Share.share(messageText, subject: 'پیام از DocAI');
  }

  void _replyToMessage(String messageId) {
    final message = currentMessages.firstWhere((msg) => msg['id'] == messageId);
    setState(() {
      _replyingToMessage = message['text'];
    });
    _focusNode.requestFocus();
    CustomSnackBar.show('در حال پاسخ به پیام...', context);
  }

  void _deleteSelectedMessages() {
    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('حذف پیام‌ها'),
          content: Text('آیا مطمئن هستید که می‌خواهید ${_selectedMessages.length} پیام را حذف کنید؟'),
          actions: [
            TextButton(
              child: const Text('لغو'),
              onPressed: () => Navigator.of(ctx).pop(),
            ),
            TextButton(
              child: Text('حذف', style: TextStyle(color: Colors.red.shade600)),
              onPressed: () {
                setState(() {
                  currentMessages.removeWhere((msg) => _selectedMessages.contains(msg['id']));
                  for (String id in _selectedMessages) {
                    _animatedMessages.remove(id);
                  }
                  _selectedMessages.clear();
                  _selectionMode = false;
                });
                Navigator.of(ctx).pop();
                CustomSnackBar.show('پیام‌ها حذف شدند', context);
              },
            ),
          ],
        );
      },
    );
  }

  void _shareSelectedMessages() {
    final selectedTexts = currentMessages
        .where((msg) => _selectedMessages.contains(msg['id']))
        .map((msg) => '${msg['sender']}: ${msg['text']}')
        .join('\n');
    
    Share.share(selectedTexts, subject: 'پیام‌های انتخاب شده از DocAI');
  }

  Widget _buildTypingIndicator() {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      child: Row(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: ChatColors.paleGreen,
            child: Icon(Icons.auto_awesome, size: 16, color: ChatColors.darkGreen),
          ),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.grey.shade200,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(4),
                bottomRight: Radius.circular(18),
              ),
            ),
            child: DefaultTextStyle(
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
              child: AnimatedTextKit(
                repeatForever: true,
                animatedTexts: [WavyAnimatedText('...')],
                isRepeatingAnimation: true,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReplyIndicator() {
    if (_replyingToMessage == null) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ChatColors.paleGreen,
        borderRadius: BorderRadius.circular(12),
        border: Border(
          right: BorderSide(color: ChatColors.primaryGreen, width: 4),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.reply, color: ChatColors.primaryGreen, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'پاسخ به:',
                  style: TextStyle(
                    color: ChatColors.darkGreen,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  _replyingToMessage!,
                  style: TextStyle(
                    color: ChatColors.darkGreen.withOpacity(0.8),
                    fontSize: 14,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.close, color: ChatColors.primaryGreen, size: 20),
            onPressed: () => setState(() => _replyingToMessage = null),
            splashRadius: 20,
          ),
        ],
      ),
    );
  }

  Widget _buildTimeoutWarning() {
    if (!_showTimeoutWarning) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.orange.shade100,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.orange.shade300),
      ),
      child: Row(
        children: [
          Icon(Icons.warning, color: Colors.orange.shade700),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'هشدار امنیتی',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.orange.shade800,
                  ),
                ),
                Text(
                  'جلسه تا $_timeoutCountdown ثانیه دیگر بسته می‌شود',
                  style: TextStyle(color: Colors.orange.shade700),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: _dismissTimeoutWarning,
            child: const Text('ادامه'),
          ),
        ],
      ),
    );
  }

  PreferredSize _buildAppBar() {
    return PreferredSize(
      preferredSize: const Size.fromHeight(_kAppBarHeight),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [ChatColors.primaryGreen, ChatColors.darkGreen],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: [
            BoxShadow(
              color: ChatColors.primaryGreen.withOpacity(0.25), 
              blurRadius: 12, 
              offset: const Offset(0, 4)
            ),
          ],
        ),
        child: SafeArea(
          bottom: false,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const AnimatedTitle(),
              Row(
                children: [
                  if (_selectionMode) ...[
                    Text(
                      '${_selectedMessages.length} انتخاب شده',
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: const Icon(Icons.share, color: Colors.white),
                      onPressed: _shareSelectedMessages,
                      splashRadius: 22,
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete, color: Colors.white),
                      onPressed: _deleteSelectedMessages,
                      splashRadius: 22,
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: _toggleSelectionMode,
                      splashRadius: 22,
                    ),
                  ] else ...[
                    IconButton(
                      icon: const Icon(Icons.add_circle_outline, color: Colors.white),
                      onPressed: _createNewSession,
                      splashRadius: 22,
                      tooltip: 'جلسه جدید',
                    ),
                    IconButton(
                      icon: const Icon(Icons.select_all, color: Colors.white),
                      onPressed: _toggleSelectionMode,
                      splashRadius: 22,
                      tooltip: 'حالت انتخاب',
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _createNewSession() async {
    if (currentSessionId != null) {
      try {
        await _chatService.endSession(currentSessionId!);
        CustomSnackBar.show('جلسه قبلی بسته شد', context);
      } catch (e) {
        // Handle error
      }
    }
    
    setState(() {
      currentSessionId = null;
      currentMessages.clear();
      _showTimeoutWarning = false;
    });
    
    _sessionTimeoutTimer?.cancel();
    _warningTimer?.cancel();
    
    await _initializeChat();
  }

  Future<void> sendMessage() async {
    final text = messageController.text.trim();
    if (text.isEmpty || currentSessionId == null) return;

    final DateTime now = DateTime.now();
    final userMessage = {
      'id': now.toIso8601String(),
      'text': text,
      'sender': 'user',
      'timestamp': now.toIso8601String(),
      'message_type': 'text',
      'replyTo': _replyingToMessage,
    };

    setState(() {
      currentMessages.add(userMessage);
      isTyping = true;
      _replyingToMessage = null;
    });

    messageController.clear();
    _scrollToBottom();
    _resetSessionTimeout();

    try {
      final botReply = await _chatService.sendMessage(
        sessionId: currentSessionId!,
        content: text,
      );

      if (!mounted) return;

      final botMessageId = DateTime.now().toIso8601String();
      final botMessage = {
        'id': botMessageId,
        'text': botReply,
        'sender': 'bot',
        'timestamp': DateTime.now().toIso8601String(),
        'message_type': 'text',
      };

      setState(() {
        currentMessages.add(botMessage);
        isTyping = false;
      });
      
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          _animatedMessages.add(botMessageId);
        }
      });
      
      _scrollToBottom();
    } catch (e) {
      if (mounted) {
        CustomSnackBar.show('خطا: $e', context, isError: true);
        setState(() => isTyping = false);
      }
    }
  }

  Future<void> _pickAndAnalyzeImage() async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );
      
      if (image == null) return;

      String caption = '';
      final result = await showDialog<String>(
        context: context,
        builder: (BuildContext context) {
          String tempCaption = '';
          return AlertDialog(
            title: const Text('توضیحات تصویر'),
            content: TextField(
              decoration: const InputDecoration(
                hintText: 'توضیحی در مورد تصویر بنویسید...',
                border: OutlineInputBorder(),
              ),
              onChanged: (value) => tempCaption = value,
              maxLines: 3,
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('انصراف'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(context, tempCaption),
                style: ElevatedButton.styleFrom(
                  backgroundColor: ChatColors.primaryGreen,
                ),
                child: const Text('ارسال'),
              ),
            ],
          );
        },
      );
      
      if (result == null) return;
      caption = result;

      final bytes = await image.readAsBytes();
      final base64Image = base64Encode(bytes);

      final userMessage = {
        'id': DateTime.now().toIso8601String(),
        'text': caption.isEmpty ? 'تصویر پزشکی' : caption,
        'sender': 'user',
        'timestamp': DateTime.now().toIso8601String(),
        'message_type': 'image',
        'image_path': kIsWeb ? null : image.path,
        'image_base64': base64Image,
      };

      setState(() {
        currentMessages.add(userMessage);
        isTyping = true;
      });

      _scrollToBottom();
      _resetSessionTimeout();

      try {
        final response = await _chatService.analyzeImage(
          imageFile: File(image.path),
          caption: caption,
        );

        if (!mounted) return;

        final botMessageId = DateTime.now().toIso8601String();
        final botMessage = {
          'id': botMessageId,
          'text': response['analysis'] ?? 'تحلیل تصویر انجام شد.',
          'sender': 'bot',
          'timestamp': DateTime.now().toIso8601String(),
          'message_type': 'text',
          'analysis': response,
        };

        setState(() {
          currentMessages.add(botMessage);
          isTyping = false;
        });

        _animatedMessages.add(botMessageId);
        _scrollToBottom();
      } catch (e) {
        if (mounted) {
          CustomSnackBar.show('خطا در تحلیل تصویر: $e', context, isError: true);
          setState(() => isTyping = false);
        }
      }
    } catch (e) {
      if (mounted) {
        CustomSnackBar.show('خطا در انتخاب تصویر: $e', context, isError: true);
        setState(() => isTyping = false);
      }
    }
  }

  Widget _buildEnhancedInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: ChatInputArea(
        messageController: messageController,
        focusNode: _focusNode,
        onSend: sendMessage,
        onPickImage: _pickAndAnalyzeImage,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ChatColors.backgroundGreen,
      appBar: _buildAppBar(),
      body: GestureDetector(
        onTap: () {
          FocusScope.of(context).unfocus();
          _resetSessionTimeout();
        },
        child: Stack(
          children: [
            const Positioned.fill(child: AnimatedBackground()),
            Column(
              children: [
                Expanded(
                  child: Stack(
                    children: [
                      ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.only(top: 16, bottom: 20),
                        itemCount: currentMessages.length,
                        itemBuilder: (ctx, idx) => ChatMessageBubble(
                          msg: currentMessages[idx],
                          index: idx,
                          animatedMessages: _animatedMessages,
                          selectedMessages: _selectedMessages,
                          selectionMode: _selectionMode,
                          onToggleSelection: _toggleMessageSelection,
                          onDelete: () => _deleteMessage(currentMessages[idx]['id']),
                          onCopy: () => _copyMessage(currentMessages[idx]['text']),
                          onShare: () => _shareMessage(currentMessages[idx]['text']),
                          onReply: () => _replyToMessage(currentMessages[idx]['id']),
                        ),
                      ),
                      if (_showScrollButton)
                        Positioned(
                          right: 16,
                          bottom: 20,
                          child: FloatingActionButton(
                            mini: true,
                            backgroundColor: ChatColors.primaryGreen,
                            elevation: 4,
                            onPressed: _scrollToBottom,
                            child: const Icon(Icons.keyboard_arrow_down, color: Colors.white),
                          ),
                        ),
                    ],
                  ),
                ),
                if (_showTimeoutWarning) _buildTimeoutWarning(),
                if (isTyping) _buildTypingIndicator(),
                _buildReplyIndicator(),
                _buildEnhancedInputArea(),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
