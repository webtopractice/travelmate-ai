/**
 * VoiceButton — microphone toggle for speech-to-text input.
 */

export default function VoiceButton({ isListening, isSupported, onToggle }) {
  if (!isSupported) return null;

  return (
    <button
      className={`btn-icon btn-voice ${isListening ? 'listening' : ''}`}
      onClick={onToggle}
      title={isListening ? 'Stop listening' : 'Start voice input'}
      type="button"
    >
      {isListening ? '⏹️' : '🎤'}
    </button>
  );
}
