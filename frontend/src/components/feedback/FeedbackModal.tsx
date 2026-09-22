import React, { useState } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, X, Loader2 } from 'lucide-react';
import { Alert } from '../../types/api';
import { useIntelligence } from '../../context/IntelligenceContext';

interface FeedbackModalProps {
  alert: Alert | null;
  onClose: () => void;
  initialAction?: 'CONFIRM' | 'REJECT';
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  alert,
  onClose,
  initialAction = 'CONFIRM',
}) => {
  const { submitFeedback } = useIntelligence();
  const [action, setAction] = useState<'CONFIRM' | 'REJECT'>(initialAction);
  const [rationale, setRationale] = useState('Cloud / shadow');
  const [analystNotes, setAnalystNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!alert) return null;

  const rejectionOptions = [
    'Cloud / shadow',
    'Seasonal variation',
    'Sensor difference',
    'False detection',
    'Other',
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const success = await submitFeedback({
      alert_id: alert.id,
      action: action,
      rationale: action === 'REJECT' ? rationale : undefined,
      analyst_notes: analystNotes.trim() || undefined,
    });
    setIsSubmitting(false);
    if (success) {
      setSubmitted(true);
      setTimeout(() => {
        onClose();
      }, 1000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-lg rounded-2xl border border-white/15 bg-[#070a10] p-6 shadow-2xl text-slate-100">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {submitted ? (
          <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
            {action === 'CONFIRM' ? (
              <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
            ) : (
              <XCircle className="w-12 h-12 text-rose-400 animate-bounce" />
            )}
            <h3 className="text-lg font-heading font-bold text-white">
              Detection {action === 'CONFIRM' ? 'Confirmed' : 'Rejected'}
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Feedback telemetry dispatched to Member 4 API and logged for retraining.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Header */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {alert.id}
                </span>
                <span className="text-xs font-mono text-emerald-400">{(alert.confidence * 100).toFixed(0)}% Confidence</span>
              </div>
              <h3 className="text-base font-heading font-bold text-white">
                Analyst Verification & Feedback
              </h3>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                {alert.locationName} &bull; {alert.type}
              </p>
            </div>

            {/* Action Toggle: Confirm vs Reject */}
            <div className="grid grid-cols-2 gap-3 p-1 rounded-xl bg-slate-950 border border-slate-800">
              <button
                type="button"
                onClick={() => setAction('CONFIRM')}
                className={`py-2.5 rounded-lg text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all ${
                  action === 'CONFIRM'
                    ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>CONFIRM DETECTION</span>
              </button>

              <button
                type="button"
                onClick={() => setAction('REJECT')}
                className={`py-2.5 rounded-lg text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all ${
                  action === 'REJECT'
                    ? 'bg-rose-500 text-slate-950 shadow-lg shadow-rose-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <XCircle className="w-4 h-4" />
                <span>REJECT DETECTION</span>
              </button>
            </div>

            {/* Conditional Rationale Options (When Rejecting) */}
            {action === 'REJECT' && (
              <div className="space-y-2 rounded-xl border border-rose-500/20 bg-rose-500/[0.04] p-3.5">
                <div className="flex items-center gap-2 text-xs font-mono font-semibold text-rose-300">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  <span>Why are you rejecting this detection?</span>
                </div>
                <div className="grid grid-cols-1 gap-1.5 pt-1">
                  {rejectionOptions.map((opt) => (
                    <label
                      key={opt}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border text-xs cursor-pointer font-mono transition-all ${
                        rationale === opt
                          ? 'border-rose-500/50 bg-rose-500/10 text-rose-200 font-semibold'
                          : 'border-slate-800 bg-slate-900/50 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <input
                        type="radio"
                        name="rationale"
                        value={opt}
                        checked={rationale === opt}
                        onChange={(e) => setRationale(e.target.value)}
                        className="accent-rose-500"
                      />
                      <span>{opt}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Analyst Observations Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Analyst Notes (Optional)
              </label>
              <textarea
                value={analystNotes}
                onChange={(e) => setAnalystNotes(e.target.value)}
                rows={2}
                placeholder="Add spectral observations or justification for retraining pipeline..."
                className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-sans"
              />
            </div>

            {/* Submit / Cancel Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-colors"
              >
                CANCEL
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className={`px-5 py-2 rounded-lg text-slate-950 font-mono font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-2 ${
                  action === 'CONFIRM'
                    ? 'bg-emerald-500 hover:bg-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                    : 'bg-rose-500 hover:bg-rose-400 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                }`}
              >
                {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>{action === 'CONFIRM' ? 'CONFIRM DETECTION' : 'SUBMIT REJECTION'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
