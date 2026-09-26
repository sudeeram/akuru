'use client';
import { useState } from 'react';
import { KeyRound, ShieldCheck } from 'lucide-react';
import { api, errorMessage } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Heading } from './shared';

export function AccountSecurity({ notify }: { notify: (message: string) => void }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  return <div className="stack"><Heading eyebrow="ACCOUNT · SECURITY" title="Change your password">Changing your password signs out every other device using your AKURU account.</Heading>
    <form className="panel stack account-security-form" onSubmit={async event => { event.preventDefault(); if (newPassword !== confirmation) { setError('The new passwords do not match.'); return; } setBusy(true); setError(''); try { await api('auth/change-known-password', { currentPassword, newPassword }); setCurrentPassword(''); setNewPassword(''); setConfirmation(''); notify('Password changed. Other signed-in devices have been signed out.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>
      <div className="panel-heading"><div><span className="pill"><ShieldCheck size={14}/> PROTECTED ACCOUNT</span><h2>Choose a new password</h2></div><KeyRound/></div>
      {error && <div className="error" role="alert">{error}</div>}
      <label className="stack" htmlFor="security-current-password"><span>Current password</span><Input id="security-current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} required/></label>
      <label className="stack" htmlFor="security-new-password"><span>New password · at least 12 characters</span><Input id="security-new-password" type="password" autoComplete="new-password" minLength={12} maxLength={200} value={newPassword} onChange={event => setNewPassword(event.target.value)} required/></label>
      <label className="stack" htmlFor="security-confirm-password"><span>Confirm new password</span><Input id="security-confirm-password" type="password" autoComplete="new-password" minLength={12} maxLength={200} value={confirmation} onChange={event => setConfirmation(event.target.value)} required/></label>
      <Button className="primary" type="submit" disabled={busy}>{busy ? 'Changing password…' : 'Change password'}</Button>
    </form>
  </div>;
}
