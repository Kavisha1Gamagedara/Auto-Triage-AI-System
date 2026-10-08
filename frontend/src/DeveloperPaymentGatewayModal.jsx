import React, { useState } from 'react';
import { 
  X, 
  CreditCard, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Lock, 
  QrCode, 
  Building, 
  Zap, 
  Download, 
  Check, 
  Clock, 
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { useAuth } from './AuthContext';

export default function DeveloperPaymentGatewayModal({
  isOpen,
  onClose,
  targetTier, // { id, name, price_lkr, price_display, limit_display }
  onPaymentSuccess
}) {
  const { user, simulatePayment } = useAuth();

  const [paymentMethod, setPaymentMethod] = useState('card'); // 'card' | 'lanka_qr' | 'bank'
  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242');
  const [cardName, setCardName] = useState(user?.name || 'Master Mechanic');
  const [expiry, setExpiry] = useState('12/28');
  const [cvv, setCvv] = useState('123');
  const [shouldFail, setShouldFail] = useState(false);

  const [processing, setProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [result, setResult] = useState(null); // { success, transaction_ref, message, ... }

  if (!isOpen || !targetTier) return null;

  const handleCheckout = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setResult(null);

    // Multi-step realistic animation
    setProcessingStep('Connecting to Central Bank & LKR clearing gateway...');
    await new Promise(r => setTimeout(r, 600));

    setProcessingStep(`Authorizing ${targetTier.price_lkr.toLocaleString()} LKR sandbox charge...`);
    await new Promise(r => setTimeout(r, 700));

    setProcessingStep('Provisioning subscription tier & updating quota limits...');
    await new Promise(r => setTimeout(r, 500));

    try {
      const res = await simulatePayment({
        tier: targetTier.id,
        payment_method: paymentMethod,
        test_card_number: cardNumber,
        test_card_name: cardName,
        test_cvv: cvv,
        should_fail: shouldFail
      });
      setResult(res);
      if (res.success && onPaymentSuccess) {
        onPaymentSuccess(res);
      }
    } catch (err) {
      setResult({
        success: false,
        message: err.message || 'Payment simulation failed.'
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleResetForNewTest = () => {
    setResult(null);
    setShouldFail(false);
  };

  return (
    <div className="gateway-modal-backdrop" onClick={onClose}>
      <div className="gateway-modal-card" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="gateway-modal-header">
          <div className="gateway-title-group">
            <div className="gateway-sandbox-badge">
              <ShieldCheck size={14} color="#10B981" />
              <span>DEVELOPER PAYMENT GATEWAY (SANDBOX)</span>
            </div>
            <h3 className="gateway-heading">Secure Checkout & Tier Provisioning</h3>
          </div>
          <button type="button" onClick={onClose} className="auth-close-btn" title="Close gateway">
            <X size={18} />
          </button>
        </div>

        {/* Processing Overlay */}
        {processing && (
          <div className="gateway-processing-overlay">
            <div className="gateway-spinner-ring" />
            <span className="gateway-processing-text">{processingStep}</span>
            <span className="gateway-processing-sub">Developer Sandbox Test Mode Active</span>
          </div>
        )}

        {/* Success Receipt View */}
        {result && result.success ? (
          <div className="gateway-receipt-view">
            <div className="receipt-success-badge">
              <CheckCircle2 size={42} color="#10B981" />
              <h4>Payment Authorized & Tier Activated!</h4>
              <p>Your subscription has been immediately provisioned in the Auto-Triage system.</p>
            </div>

            <div className="receipt-details-slip">
              <div className="receipt-row">
                <span className="receipt-label">Transaction Ref:</span>
                <strong className="receipt-val mono">{result.transaction_ref}</strong>
              </div>
              <div className="receipt-row">
                <span className="receipt-label">Tier Activated:</span>
                <strong className="receipt-val">{targetTier.name}</strong>
              </div>
              <div className="receipt-row">
                <span className="receipt-label">Amount Paid:</span>
                <strong className="receipt-val highlight">{Number(result.amount_lkr).toLocaleString()} LKR</strong>
              </div>
              <div className="receipt-row">
                <span className="receipt-label">Payment Method:</span>
                <span className="receipt-val">{result.payment_method.toUpperCase()} (Sandbox)</span>
              </div>
              <div className="receipt-row">
                <span className="receipt-label">New Quota:</span>
                <strong className="receipt-val text-green">{targetTier.limit_display}</strong>
              </div>
              <div className="receipt-row">
                <span className="receipt-label">Status:</span>
                <span className="receipt-status-pill">SUCCEEDED // ACTIVE</span>
              </div>
            </div>

            <div className="receipt-action-buttons">
              <button 
                type="button" 
                onClick={onClose} 
                className="receipt-btn-primary"
              >
                <Zap size={14} />
                <span>Start Diagnosing Vehicles</span>
              </button>
              <button 
                type="button" 
                onClick={handleResetForNewTest} 
                className="receipt-btn-secondary"
              >
                <span>Test Another Transaction</span>
              </button>
            </div>
          </div>
        ) : result && !result.success ? (
          /* Decline / Error View */
          <div className="gateway-declined-view">
            <div className="declined-badge">
              <XCircle size={42} color="#EF4444" />
              <h4>Payment Declined (Simulation)</h4>
              <p>{result.message || 'The test payment was declined by the developer sandbox trigger.'}</p>
            </div>
            <button 
              type="button" 
              onClick={handleResetForNewTest} 
              className="receipt-btn-primary"
            >
              <span>Try Again with Valid Test Card</span>
            </button>
          </div>
        ) : (
          /* Payment Form View */
          <form onSubmit={handleCheckout} className="gateway-form-body">
            {/* Plan Summary Bar */}
            <div className="gateway-plan-summary">
              <div className="plan-summary-left">
                <span className="summary-target-label">Upgrading To:</span>
                <strong className="summary-target-name">{targetTier.name}</strong>
                <span className="summary-target-quota">{targetTier.limit_display}</span>
              </div>
              <div className="plan-summary-right">
                <span className="summary-amount-label">Total Due Today:</span>
                <strong className="summary-amount-val">{Number(targetTier.price_lkr).toLocaleString()} LKR</strong>
                <span className="summary-amount-cadence">Billed monthly</span>
              </div>
            </div>

            {/* Payment Method Selector */}
            <div className="gateway-method-selector">
              <button
                type="button"
                className={`gateway-method-btn ${paymentMethod === 'card' ? 'active' : ''}`}
                onClick={() => setPaymentMethod('card')}
              >
                <CreditCard size={15} />
                <span>Test Card (Visa/Mastercard)</span>
              </button>
              <button
                type="button"
                className={`gateway-method-btn ${paymentMethod === 'lanka_qr' ? 'active' : ''}`}
                onClick={() => setPaymentMethod('lanka_qr')}
              >
                <QrCode size={15} />
                <span>LankaQR (Simulated)</span>
              </button>
              <button
                type="button"
                className={`gateway-method-btn ${paymentMethod === 'bank' ? 'active' : ''}`}
                onClick={() => setPaymentMethod('bank')}
              >
                <Building size={15} />
                <span>Bank Settlement</span>
              </button>
            </div>

            {/* Card Inputs */}
            {paymentMethod === 'card' && (
              <div className="gateway-card-inputs">
                <div className="gateway-input-group">
                  <label className="gateway-label">Card Number (Developer Test Sandbox)</label>
                  <div className="gateway-input-wrapper">
                    <CreditCard size={14} className="input-icon" />
                    <input
                      type="text"
                      required
                      value={cardNumber}
                      onChange={e => setCardNumber(e.target.value)}
                      placeholder="4242 4242 4242 4242"
                      className="gateway-input"
                    />
                    <span className="test-card-tag">TEST CARD</span>
                  </div>
                </div>

                <div className="gateway-input-row">
                  <div className="gateway-input-group">
                    <label className="gateway-label">Cardholder Name</label>
                    <input
                      type="text"
                      required
                      value={cardName}
                      onChange={e => setCardName(e.target.value)}
                      placeholder="Master Mechanic"
                      className="gateway-input"
                    />
                  </div>
                  <div className="gateway-input-group">
                    <label className="gateway-label">Expires</label>
                    <input
                      type="text"
                      required
                      value={expiry}
                      onChange={e => setExpiry(e.target.value)}
                      placeholder="MM/YY"
                      className="gateway-input"
                    />
                  </div>
                  <div className="gateway-input-group">
                    <label className="gateway-label">CVV</label>
                    <input
                      type="text"
                      required
                      value={cvv}
                      onChange={e => setCvv(e.target.value)}
                      placeholder="123"
                      className="gateway-input"
                    />
                  </div>
                </div>
              </div>
            )}

            {paymentMethod === 'lanka_qr' && (
              <div className="gateway-qr-view">
                <div className="qr-box">
                  <QrCode size={120} color="#00F0FF" />
                </div>
                <div className="qr-info">
                  <strong>Simulated LankaQR Gateway Payment</strong>
                  <p>Scan to test instant LKR debit settlement from Sri Lankan banking apps (Commercial, HNB, Sampath).</p>
                </div>
              </div>
            )}

            {paymentMethod === 'bank' && (
              <div className="gateway-bank-view">
                <div className="bank-slip">
                  <p><strong>Bank:</strong> Commercial Bank of Ceylon PLC</p>
                  <p><strong>Account Name:</strong> Auto-Triage AI Systems (Pvt) Ltd</p>
                  <p><strong>Account Number:</strong> 8009-4242-9901</p>
                  <p><strong>Branch:</strong> Colombo 03 Corporate Branch</p>
                </div>
              </div>
            )}

            {/* Developer Testing Controls Toggle */}
            <div className="gateway-dev-controls-box">
              <span className="dev-controls-title">// DEVELOPER SANDBOX SIMULATION TOGGLES:</span>
              <label className="dev-toggle-row">
                <input
                  type="checkbox"
                  checked={shouldFail}
                  onChange={e => setShouldFail(e.target.checked)}
                />
                <span className="dev-toggle-text">
                  Simulate Card Decline / Transaction Failure (Test Error Handling)
                </span>
              </label>
            </div>

            {/* Submit Button */}
            <button type="submit" disabled={processing} className="gateway-submit-btn">
              <Lock size={14} />
              <span>
                {shouldFail 
                  ? `TRIGGER SIMULATED DECLINE (${Number(targetTier.price_lkr).toLocaleString()} LKR)` 
                  : `AUTHORIZE & PAY ${Number(targetTier.price_lkr).toLocaleString()} LKR (SANDBOX)`}
              </span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
