import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:krish_ai/features/ai_assistant/presentation/widgets/ai_avatar_widget.dart';

class Voice {
  final String id;
  final String name;
  final String accent;
  final String gender;
  final String preview;

  Voice({
    required this.id,
    required this.name,
    required this.accent,
    required this.gender,
    required this.preview,
  });
}

class VoiceSettings {
  final double pitch;
  final double speed;
  final double volume;

  VoiceSettings({
    this.pitch = 1.0,
    this.speed = 1.0,
    this.volume = 1.0,
  });
}

class VoiceCustomizationWidget extends StatefulWidget {
  final Function(Voice) onVoiceSelect;
  final Function(VoiceSettings) onSettingsChange;

  const VoiceCustomizationWidget({
    super.key,
    required this.onVoiceSelect,
    required this.onSettingsChange,
  });

  @override
  State<VoiceCustomizationWidget> createState() => _VoiceCustomizationWidgetState();
}

class _VoiceCustomizationWidgetState extends State<VoiceCustomizationWidget> {
  final List<Voice> _voices = [
    Voice(
      id: 'en-US-1',
      name: 'Sarah',
      accent: 'American',
      gender: 'Female',
      preview: 'Hello, I am Sarah, your AI assistant.',
    ),
    Voice(
      id: 'en-GB-1',
      name: 'James',
      accent: 'British',
      gender: 'Male',
      preview: 'Hello, I am James, your AI assistant.',
    ),
    Voice(
      id: 'en-AU-1',
      name: 'Emma',
      accent: 'Australian',
      gender: 'Female',
      preview: 'Hello, I am Emma, your AI assistant.',
    ),
    Voice(
      id: 'en-IN-1',
      name: 'Raj',
      accent: 'Indian',
      gender: 'Male',
      preview: 'Hello, I am Raj, your AI assistant.',
    ),
  ];

  late Voice _selectedVoice;
  late VoiceSettings _settings;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    _selectedVoice = _voices[0];
    _settings = VoiceSettings();
  }

  void _playPreview() async {
    setState(() => _isPlaying = true);
    await Future.delayed(const Duration(seconds: 2));
    setState(() => _isPlaying = false);
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Choose a Voice',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          _buildVoiceGrid(),
          const SizedBox(height: 32),
          Text(
            'Voice Settings',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          _buildVoiceSettings(),
          const SizedBox(height: 32),
          Center(
            child: AIAvatarWidget(
              size: 120,
              emotion: _isPlaying ? AvatarEmotion.speaking : AvatarEmotion.neutral,
              isSpeaking: _isPlaying,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: _voices.length,
      itemBuilder: (context, index) {
        final voice = _voices[index];
        final isSelected = voice.id == _selectedVoice.id;

        return GestureDetector(
          onTap: () {
            setState(() => _selectedVoice = voice);
            widget.onVoiceSelect(voice);
          },
          child: Container(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected
                    ? Theme.of(context).colorScheme.primary
                    : Colors.transparent,
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  voice.name,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  voice.accent,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 8),
                ElevatedButton(
                  onPressed: _playPreview,
                  child: Text(_isPlaying ? 'Playing...' : 'Preview'),
                ),
              ],
            ),
          ).animate(target: isSelected ? 1 : 0)
            .scale(
              begin: const Offset(1, 1),
              end: const Offset(1.05, 1.05),
              duration: const Duration(milliseconds: 200),
            ),
        );
      },
    );
  }

  Widget _buildVoiceSettings() {
    return Column(
      children: [
        _buildSliderSetting(
          label: 'Pitch',
          value: _settings.pitch,
          onChanged: (value) {
            setState(() {
              _settings = VoiceSettings(
                pitch: value,
                speed: _settings.speed,
                volume: _settings.volume,
              );
            });
            widget.onSettingsChange(_settings);
          },
        ),
        const SizedBox(height: 16),
        _buildSliderSetting(
          label: 'Speed',
          value: _settings.speed,
          onChanged: (value) {
            setState(() {
              _settings = VoiceSettings(
                pitch: _settings.pitch,
                speed: value,
                volume: _settings.volume,
              );
            });
            widget.onSettingsChange(_settings);
          },
        ),
        const SizedBox(height: 16),
        _buildSliderSetting(
          label: 'Volume',
          value: _settings.volume,
          onChanged: (value) {
            setState(() {
              _settings = VoiceSettings(
                pitch: _settings.pitch,
                speed: _settings.speed,
                volume: value,
              );
            });
            widget.onSettingsChange(_settings);
          },
        ),
      ],
    );
  }

  Widget _buildSliderSetting({
    required String label,
    required double value,
    required ValueChanged<double> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: Theme.of(context).textTheme.titleSmall),
            Text(value.toStringAsFixed(1)),
          ],
        ),
        Slider(
          value: value,
          min: 0.5,
          max: 2.0,
          divisions: 15,
          onChanged: onChanged,
        ),
      ],
    );
  }
}
