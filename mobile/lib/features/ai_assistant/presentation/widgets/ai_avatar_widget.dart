import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import 'package:rive/rive.dart';
import 'package:flutter_animate/flutter_animate.dart';

enum AvatarEmotion {
  neutral,
  happy,
  thinking,
  listening,
  speaking
}

class AIAvatarWidget extends StatefulWidget {
  final double size;
  final AvatarEmotion emotion;
  final bool isSpeaking;
  final bool isListening;
  final VoidCallback? onTap;

  const AIAvatarWidget({
    super.key,
    this.size = 200,
    this.emotion = AvatarEmotion.neutral,
    this.isSpeaking = false,
    this.isListening = false,
    this.onTap,
  });

  @override
  State<AIAvatarWidget> createState() => _AIAvatarWidgetState();
}

class _AIAvatarWidgetState extends State<AIAvatarWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late RiveAnimationController _riveController;
  late StateMachineController _stateMachineController;
  SMITrigger? _emotionTrigger;
  SMIBool? _speakingInput;
  SMIBool? _listeningInput;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
  }

  void _setupAnimations() {
    // Setup pulse animation
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    // Setup Rive controller
    _riveController = SimpleAnimation('idle');
  }

  void _onRiveInit(Artboard artboard) {
    _stateMachineController = StateMachineController.fromArtboard(
      artboard,
      'AI_State_Machine',
    )!;
    artboard.addController(_stateMachineController);

    _emotionTrigger = _stateMachineController.findSMI('emotion_trigger');
    _speakingInput = _stateMachineController.findSMI('is_speaking');
    _listeningInput = _stateMachineController.findSMI('is_listening');

    _updateEmotionState();
  }

  void _updateEmotionState() {
    if (_emotionTrigger == null) return;

    switch (widget.emotion) {
      case AvatarEmotion.happy:
        _emotionTrigger!.fire();
        break;
      case AvatarEmotion.thinking:
        _emotionTrigger!.fire();
        break;
      case AvatarEmotion.listening:
        _emotionTrigger!.fire();
        break;
      default:
        break;
    }

    _speakingInput?.value = widget.isSpeaking;
    _listeningInput?.value = widget.isListening;
  }

  @override
  void didUpdateWidget(AIAvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.emotion != widget.emotion ||
        oldWidget.isSpeaking != widget.isSpeaking ||
        oldWidget.isListening != widget.isListening) {
      _updateEmotionState();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _stateMachineController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Glowing background
          AnimatedBuilder(
            animation: _pulseController,
            builder: (context, child) {
              return Container(
                width: widget.size * 1.2,
                height: widget.size * 1.2,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      Theme.of(context).colorScheme.primary.withOpacity(0.2),
                      Theme.of(context).colorScheme.primary.withOpacity(0),
                    ],
                    stops: const [0.5, 1.0],
                  ),
                ),
              ).animate()
                .scale(
                  begin: const Offset(0.95, 0.95),
                  end: const Offset(1.05, 1.05),
                  duration: const Duration(milliseconds: 1500),
                  curve: Curves.easeInOut,
                )
                .repeat(reverse: true);
            },
          ),

          // Main avatar container
          Container(
            width: widget.size,
            height: widget.size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Theme.of(context).colorScheme.primary,
                  Theme.of(context).colorScheme.secondary,
                ],
              ),
              boxShadow: [
                BoxShadow(
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                  blurRadius: 20,
                  spreadRadius: 5,
                ),
              ],
            ),
            child: ClipOval(
              child: Stack(
                children: [
                  // Rive animation
                  RiveAnimation.asset(
                    'assets/animations/ai_avatar.riv',
                    controllers: [_riveController],
                    onInit: _onRiveInit,
                    fit: BoxFit.cover,
                  ),

                  // Overlay effects
                  if (widget.isListening)
                    Positioned.fill(
                      child: _buildListeningEffect(),
                    ),
                  if (widget.isSpeaking)
                    Positioned.fill(
                      child: _buildSpeakingEffect(),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListeningEffect() {
    return CustomPaint(
      painter: ListeningEffectPainter(
        color: Theme.of(context).colorScheme.primary,
        amplitude: _pulseController.value * 20,
      ),
    );
  }

  Widget _buildSpeakingEffect() {
    return Lottie.asset(
      'assets/animations/wave_form.json',
      fit: BoxFit.cover,
    );
  }
}

class ListeningEffectPainter extends CustomPainter {
  final Color color;
  final double amplitude;

  ListeningEffectPainter({
    required this.color,
    required this.amplitude,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final path = Path();
    var x = 0.0;
    final points = <Offset>[];

    while (x < size.width) {
      final y = size.height / 2 +
          amplitude * sin((x + DateTime.now().millisecondsSinceEpoch / 200) / 20);
      points.add(Offset(x, y));
      x += 5;
    }

    path.moveTo(points.first.dx, points.first.dy);
    for (var i = 1; i < points.length; i++) {
      final p0 = points[i - 1];
      final p1 = points[i];
      path.quadraticBezierTo(
        p0.dx,
        p0.dy,
        (p0.dx + p1.dx) / 2,
        (p0.dy + p1.dy) / 2,
      );
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(ListeningEffectPainter oldDelegate) =>
      color != oldDelegate.color || amplitude != oldDelegate.amplitude;
}
