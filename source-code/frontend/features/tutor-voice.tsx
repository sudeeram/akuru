'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Pause, Play, RotateCcw, Snail, Square, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  createRealtimeCredential,
  errorMessage,
  saveRealtimeTranscriptTurn,
  updateRealtimeState,
  type RealtimeLanguageMode,
} from '@/lib/api';

type Props = {
  sessionRef: string;
  subjectId: string;
  profileIdentity: string;
  disabled: boolean;
  notify: (message: string) => void;
  onTranscript: () => Promise<void>;
  focusText: () => void;
};

export function TutorVoice({ sessionRef, subjectId, profileIdentity, disabled, notify, onTranscript, focusText }: Props) {
  const peer = useRef<RTCPeerConnection | null>(null), channel = useRef<RTCDataChannel | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null), connectionRef = useRef<string | null>(null);
  const activeProfile = useRef(profileIdentity), reconnecting = useRef(false), assistantCaption = useRef('');
  const [state, setState] = useState<'idle' | 'connecting' | 'live' | 'paused'>('idle');
  const [muted, setMuted] = useState(false), [caption, setCaption] = useState(''), [error, setError] = useState('');
  const [languageMode, setLanguageMode] = useState<RealtimeLanguageMode>(subjectId === 'french' ? 'french_conversation' : 'auto');
  const key = () => crypto.randomUUID();

  const close = useCallback(async (finalState: 'ended' | 'failed' | 'cancelled' = 'ended') => {
    const ref = connectionRef.current;
    connectionRef.current = null;
    channel.current?.close(); channel.current = null;
    peer.current?.getSenders().forEach((sender) => sender.track?.stop());
    peer.current?.close(); peer.current = null;
    if (audio.current) { audio.current.srcObject = null; audio.current.remove(); audio.current = null; }
    if (ref) await updateRealtimeState(ref, finalState, finalState === 'failed' ? 'webrtc_connection_failed' : undefined).catch(() => undefined);
  }, []);

  const start = useCallback(async (failedRef?: string) => {
    if (disabled || reconnecting.current) return;
    reconnecting.current = true; setState('connecting'); setError(''); setCaption('Connecting securely…');
    try {
      const credential = await createRealtimeCredential(sessionRef, key(), languageMode, failedRef);
      connectionRef.current = credential.connectionRef;
      const pc = new RTCPeerConnection(); peer.current = pc;
      const player = document.createElement('audio'); player.autoplay = true; player.hidden = true;
      document.body.appendChild(player); audio.current = player;
      pc.ontrack = (event) => { player.srcObject = event.streams[0]; };
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));
      const dc = pc.createDataChannel('oai-events'); channel.current = dc;
      dc.onopen = async () => { setState('live'); setCaption('Listening…'); notify(credential.reconnect ? 'Voice reconnected with your saved context.' : 'Voice tutor connected.'); await updateRealtimeState(credential.connectionRef, 'connected'); };
      dc.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'conversation.item.input_audio_transcription.completed' && message.transcript?.trim()) {
          setCaption(`You: ${message.transcript.trim()}`);
          void saveRealtimeTranscriptTurn(credential.connectionRef, 'student', message.transcript.trim(), `voice-in-${message.item_id || key()}`).then(onTranscript);
        }
        if (message.type === 'response.output_audio_transcript.delta') {
          assistantCaption.current += message.delta || ''; setCaption(assistantCaption.current);
        }
        if (message.type === 'response.output_audio_transcript.done') {
          const text = (message.transcript || assistantCaption.current).trim(); assistantCaption.current = '';
          if (text) void saveRealtimeTranscriptTurn(credential.connectionRef, 'assistant', text, `voice-out-${message.item_id || message.response_id || key()}`).then(onTranscript);
        }
      };
      pc.onconnectionstatechange = () => {
        if (['failed', 'disconnected'].includes(pc.connectionState) && connectionRef.current === credential.connectionRef) {
          void close('failed').then(() => start(credential.connectionRef));
        }
      };
      const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
      const answer = await fetch('https://api.openai.com/v1/realtime/calls', {
        method: 'POST', body: offer.sdp, headers: { Authorization: `Bearer ${credential.clientSecret}`, 'Content-Type': 'application/sdp' },
      });
      if (!answer.ok) throw new Error('The secure voice connection could not be established.');
      await pc.setRemoteDescription({ type: 'answer', sdp: await answer.text() });
    } catch (cause) {
      await close('cancelled'); setState('idle'); setError(errorMessage(cause));
    } finally { reconnecting.current = false; }
  }, [close, disabled, languageMode, notify, onTranscript, sessionRef]);

  useEffect(() => () => { void close('ended'); }, [close]);
  useEffect(() => {
    if (activeProfile.current !== profileIdentity) {
      activeProfile.current = profileIdentity;
      const failed = connectionRef.current;
      if (failed) void close('ended').then(() => start());
    }
  }, [close, profileIdentity, start]);

  const send = (event: object) => { if (channel.current?.readyState === 'open') channel.current.send(JSON.stringify(event)); };
  return <section className="panel stack tutor-voice" aria-label="Realtime voice tutor">
    <div className="panel-heading"><div><span className="pill"><Mic size={13} /> REALTIME VOICE</span><h2>Talk with your tutor</h2></div><span aria-live="polite">{state === 'live' ? 'Connected' : state}</span></div>
    {subjectId === 'french' && <label className="tutor-mode"><span>French activity</span><select value={languageMode} disabled={state !== 'idle'} onChange={(event) => setLanguageMode(event.target.value as RealtimeLanguageMode)}><option value="french_conversation">Conversation</option><option value="french_vocabulary">Vocabulary</option><option value="french_pronunciation">Pronunciation</option></select></label>}
    <div className="voice-caption" aria-live="polite">{caption || 'Live captions will appear here. No raw audio is stored.'}</div>
    {error && <div className="error" role="alert">{error}</div>}
    <div className="button-row">
      {state === 'idle' && <Button className="primary" disabled={disabled} onClick={() => void start()}><Play size={15} />Start voice</Button>}
      {state === 'paused' && <Button className="primary" disabled={disabled} onClick={() => void start()}><Play size={15} />Resume</Button>}
      {state === 'live' && <Button variant="outline" onClick={() => void close('ended').then(() => setState('paused'))}><Pause size={15} />Pause</Button>}
      {state === 'live' && <Button variant="outline" onClick={() => { const track = peer.current?.getSenders().find((item) => item.track?.kind === 'audio')?.track; if (track) { track.enabled = muted; setMuted(!muted); } }}>{muted ? <Mic size={15} /> : <MicOff size={15} />}{muted ? 'Unmute' : 'Mute'}</Button>}
      {state === 'live' && <Button variant="outline" onClick={() => { send({ type: 'response.cancel' }); send({ type: 'output_audio_buffer.clear' }); }}><Square size={15} />Interrupt</Button>}
      {state === 'live' && <Button variant="outline" onClick={() => send({ type: 'response.create', response: { instructions: 'Repeat your previous explanation more briefly.' } })}><RotateCcw size={15} />Repeat</Button>}
      {state === 'live' && <Button variant="outline" onClick={() => send({ type: 'session.update', session: { type: 'realtime', audio: { output: { speed: 0.85 } } } })}><Snail size={15} />Slower</Button>}
      {state !== 'idle' && <Button variant="outline" onClick={() => void close('ended').then(() => { setState('idle'); setCaption('Voice ended.'); })}><Volume2 size={15} />End voice</Button>}
      <Button variant="outline" onClick={focusText}>Use text instead</Button>
    </div>
    <small>Voice works during practice only. AKURU stores captions and connection usage, never microphone audio.</small>
  </section>;
}
