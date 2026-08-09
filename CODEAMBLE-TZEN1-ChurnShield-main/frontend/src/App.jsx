import { useMemo, useState, useRef } from "react";
import axios from "axios";
import {
  ShieldCheck, Upload, UserRound, BarChart3, Download, Building2, Tv, PhoneCall,
  Mail, Users, Search, Sparkles, ArrowRight, ChevronLeft, AlertTriangle,
  CheckCircle2, FileText, X, Copy, Check, BrainCircuit, Activity, TrendingUp,
  TrendingDown, Eye, Shield, Zap, Clock, Target, LayoutDashboard, BookOpen,
  ChevronRight, RefreshCw, Star, Wifi, PlayCircle, Landmark, BarChart2, Lightbulb,
  MessageSquare, UserCheck
} from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from "recharts";
import "./index.css";

/* ─────────── CONSTANTS ─────────── */
const DOMAIN_FIELDS = {
  telecom: [
    { key: "Age", label: "Age", type: "number", min: 18, max: 90 },
    { key: "Gender", label: "Gender", type: "select", options: ["Male", "Female"] },
    { key: "Tenure in Months", label: "Tenure (Months)", type: "number", min: 0, max: 130 },
    { key: "Contract", label: "Contract Type", type: "select", options: ["Month-to-Month", "One Year", "Two Year"] },
    { key: "Internet Type", label: "Internet Type", type: "select", options: ["DSL", "Fiber Optic", "Cable", "None"] },
    { key: "Payment Method", label: "Payment Method", type: "select", options: ["Bank Withdrawal", "Credit Card", "Mailed Check"] },
    { key: "Monthly Charge", label: "Monthly Charges ($)", type: "number", min: 0, max: 500, step: 0.01 },
    { key: "Satisfaction Score", label: "Satisfaction Score (1-5)", type: "number", min: 1, max: 5 },
    { key: "Online Security", label: "Online Security", type: "select", options: ["0", "1"], labels: ["No", "Yes"] },
    { key: "Premium Tech Support", label: "Premium Tech Support", type: "select", options: ["0", "1"], labels: ["No", "Yes"] },
    { key: "Number of Referrals", label: "Number of Referrals", type: "number", min: 0, max: 20 },
    { key: "Internet Service", label: "Has Internet Service", type: "select", options: ["0", "1"], labels: ["No", "Yes"] },
    { key: "Married", label: "Married", type: "select", options: ["0", "1"], labels: ["No", "Yes"] },
  ],
  ott: [
    { key: "Age", label: "Age", type: "number", min: 18, max: 80 },
    { key: "Gender", label: "Gender", type: "select", options: ["Male", "Female"] },
    { key: "Subscription Type", label: "Subscription Type", type: "select", options: ["Basic", "Standard", "Premium"] },
    { key: "Monthly Charge", label: "Monthly Charge ($)", type: "number", min: 0, max: 100, step: 0.01 },
    { key: "Tenure Months", label: "Tenure (Months)", type: "number", min: 0, max: 100 },
    { key: "Avg Monthly Watch Hours", label: "Avg Watch Hours/Month", type: "number", min: 0, max: 300, step: 0.1 },
    { key: "Days Since Last Login", label: "Days Since Last Login", type: "number", min: 0, max: 365 },
    { key: "Profile Count", label: "Profiles Count", type: "number", min: 1, max: 5 },
    { key: "Devices Registered", label: "Devices Registered", type: "number", min: 1, max: 10 },
    { key: "Support Tickets", label: "Support Tickets", type: "number", min: 0, max: 20 },
  ],
  banking: [
    { key: "Customer_Age", label: "Customer Age", type: "number", min: 18, max: 90 },
    { key: "Gender", label: "Gender", type: "select", options: ["M", "F"] },
    { key: "Dependent_count", label: "Dependent Count", type: "number", min: 0, max: 10 },
    { key: "Education_Level", label: "Education Level", type: "select", options: ["Uneducated","High School","College","Graduate","Post-Graduate","Doctorate","Unknown"] },
    { key: "Marital_Status", label: "Marital Status", type: "select", options: ["Single","Married","Divorced","Unknown"] },
    { key: "Income_Category", label: "Income Category", type: "select", options: ["Less than $40K","$40K - $60K","$60K - $80K","$80K - $120K","$120K +","Unknown"] },
    { key: "Card_Category", label: "Card Category", type: "select", options: ["Blue","Silver","Gold","Platinum"] },
    { key: "Months_on_book", label: "Months on Book", type: "number", min: 0, max: 100 },
    { key: "Total_Relationship_Count", label: "Relationship Count", type: "number", min: 1, max: 10 },
    { key: "Months_Inactive_12_mon", label: "Months Inactive (12mo)", type: "number", min: 0, max: 12 },
    { key: "Contacts_Count_12_mon", label: "Contacts (12mo)", type: "number", min: 0, max: 20 },
    { key: "Credit_Limit", label: "Credit Limit", type: "number", min: 1000, max: 50000, step: 100 },
    { key: "Total_Revolving_Bal", label: "Revolving Balance", type: "number", min: 0, max: 5000, step: 10 },
    { key: "Total_Trans_Amt", label: "Total Transaction Amount", type: "number", min: 0, max: 20000, step: 10 },
    { key: "Total_Trans_Ct", label: "Transaction Count", type: "number", min: 0, max: 200 },
    { key: "Avg_Utilization_Ratio", label: "Avg Utilization Ratio", type: "number", min: 0, max: 1, step: 0.001 },
  ]
};

const DOMAIN_DEFAULTS = {
  telecom: { Age: 35, "Monthly Charge": 85.0, Contract: "Month-to-Month", "Satisfaction Score": 2, "Tenure in Months": 5, "Number of Referrals": 0, "Online Security": "0", "Premium Tech Support": "0", "Internet Type": "Fiber Optic", "Payment Method": "Bank Withdrawal", Gender: "Male", "Internet Service": "1", Married: "0" },
  ott: { Age: 29, "Monthly Charge": 15.49, "Subscription Type": "Standard", "Tenure Months": 6, "Avg Monthly Watch Hours": 12.5, "Days Since Last Login": 18, "Profile Count": 2, "Devices Registered": 4, "Support Tickets": 2, Gender: "Female" },
  banking: { Customer_Age: 45, Gender: "M", Dependent_count: 3, Education_Level: "Graduate", Marital_Status: "Married", Income_Category: "$60K - $80K", Card_Category: "Blue", Months_on_book: 36, Total_Relationship_Count: 4, Months_Inactive_12_mon: 3, Contacts_Count_12_mon: 2, Credit_Limit: 12000.0, Total_Revolving_Bal: 1500.0, Avg_Open_To_Buy: 10500.0, Total_Amt_Chng_Q4_Q1: 1.2, Total_Trans_Amt: 4500.0, Total_Trans_Ct: 42, Total_Ct_Chng_Q4_Q1: 1.5, Avg_Utilization_Ratio: 0.125 }
};

const RISK_COLORS = { CRITICAL: "#EF4444", HIGH: "#F97316", MEDIUM: "#8B5CF6", LOW: "#10B981" };

const INDUSTRY_META = {
  telecom: {
    label: "Telecom", Icon: Wifi, emoji: "📡", color: "indigo",
    hasRevenueRisk: true, exposureLabel: "Revenue at Risk",
    desc: "Analyze subscriber churn, customer engagement, service experience, and revenue exposure.",
    tags: ["Churn Prediction", "Customer Risk", "Revenue Risk"],
    tagStyles: ["cs-tag-indigo", "cs-tag-purple", "cs-tag-orange"]
  },
  ott: {
    label: "OTT & Streaming", Icon: PlayCircle, emoji: "🎬", color: "purple",
    hasRevenueRisk: true, exposureLabel: "Subscription Exposure",
    desc: "Analyze subscriber engagement, viewing behavior, inactivity, subscription risk, and revenue exposure.",
    tags: ["Churn Prediction", "Engagement Risk", "Revenue Risk"],
    tagStyles: ["cs-tag-indigo", "cs-tag-purple", "cs-tag-orange"]
  },
  banking: {
    label: "Banking", Icon: Landmark, emoji: "🏦", color: "emerald",
    hasRevenueRisk: false, exposureLabel: "Transaction At Risk",
    desc: "Analyze customer attrition, transaction behavior, inactivity, relationship depth, and customer risk.",
    tags: ["Churn Prediction", "Behavioral Risk", "Customer Intelligence"],
    tagStyles: ["cs-tag-indigo", "cs-tag-purple", "cs-tag-green"]
  }
};

const NAV_ITEMS = [
  { id: "input", label: "Input", Icon: Upload },
  { id: "dashboard", label: "Dashboard", Icon: LayoutDashboard },
  { id: "customer_portfolio", label: "Portfolio", Icon: ShieldCheck },
  { id: "retention", label: "Retention", Icon: Shield },
];

const ITEMS_PER_PAGE = 15;

/* ─────────── HELPERS ─────────── */
const sanitizeFloat = (v) => (isNaN(v) || !isFinite(v) ? 0 : parseFloat(v));

const RiskBadge = ({ level }) => {
  const cls = { CRITICAL: "badge-critical", HIGH: "badge-high", MEDIUM: "badge-medium", LOW: "badge-low" };
  const icons = { CRITICAL: "🔴", HIGH: "🟠", MEDIUM: "🟣", LOW: "🟢" };
  return <span className={cls[level] || "badge-medium"}>{icons[level]} {level}</span>;
};

const ChurnMeter = ({ prob }) => {
  const pct = Math.round(prob * 100);
  const color = pct >= 80 ? "#EF4444" : pct >= 60 ? "#F97316" : pct >= 30 ? "#8B5CF6" : "#10B981";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>Churn Probability</span>
        <span style={{ fontSize: 28, fontWeight: 800, color }}>{pct}%</span>
      </div>
      <div className="churn-meter-track">
        <div className="churn-meter-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
};

/* ─────────── MAIN APP ─────────── */
export default function App() {
  const [industry, setIndustry] = useState("telecom");
  const [page, setPage] = useState("industry");
  const [prevPage, setPrevPage] = useState(null);
  const [loading, setLoading] = useState(false);
  // Per-industry upload statuses so each domain tracks its own
  const [uploadStatuses, setUploadStatuses] = useState({ telecom: null, ott: null, banking: null });
  const uploadStatus = uploadStatuses[industry];
  const setUploadStatus = (v) => setUploadStatuses((p) => ({ ...p, [industry]: v }));

  const [form, setForm] = useState(DOMAIN_DEFAULTS.telecom);

  // ── Per-industry persistent data ──────────────────────────────────────
  // Data is NEVER wiped when switching industries. Switching back restores
  // previously uploaded results automatically.
  const [allBulkResults, setAllBulkResults] = useState({ telecom: null, ott: null, banking: null });
  const bulkResult = allBulkResults[industry];
  const setBulkResult = (v) => setAllBulkResults((p) => ({ ...p, [industry]: v }));

  const [allInspectedCustomers, setAllInspectedCustomers] = useState({ telecom: [], ott: [], banking: [] });
  const inspectedCustomers = allInspectedCustomers[industry];

  const [allRetainedCustomers, setAllRetainedCustomers] = useState({ telecom: [], ott: [], banking: [] });
  const retainedCustomers = allRetainedCustomers[industry] || [];
  // ─────────────────────────────────────────────────────────────────────

  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [strategyResult, setStrategyResult] = useState(null);
  const [commResult, setCommResult] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("churn_probability");
  const shuffleSeedRef = useRef(Math.random());
  const [currentPage, setCurrentPage] = useState(1);
  const [commChannel, setCommChannel] = useState("email");
  const [commTone, setCommTone] = useState("professional");
  const [copied, setCopied] = useState(false);
  const [showReqModal, setShowReqModal] = useState(false);

  const fileInputRef = useRef(null);
  const currentMeta = INDUSTRY_META[industry];

  /* Navigation */
  const navigate = (dest) => { setPrevPage(page); setPage(dest); };
  const goBack = () => { if (prevPage) { setPage(prevPage); setPrevPage(null); } else navigate("dashboard"); };

  const selectIndustry = (ind) => {
    setIndustry(ind);
    setForm(DOMAIN_DEFAULTS[ind] || {});
    setSelectedCustomer(null); setStrategyResult(null);
    setCommResult(null); setSearchQuery("");
    setRiskFilter("ALL"); setCurrentPage(1);
    const existingResult = allBulkResults[ind];
    navigate(existingResult ? "dashboard" : "input");
  };

  const markInspected = (cust) => {
    setAllInspectedCustomers((prev) => {
      const current = prev[industry] || [];
      if (current.find((c) => c.customer_id === cust.customer_id)) return prev;
      return { ...prev, [industry]: [cust, ...current] };
    });
  };

  const markRetained = (cust) => {
    if (!cust || !cust.customer_id) return;
    setAllRetainedCustomers((prev) => {
      const current = prev[industry] || [];
      if (current.find((c) => c.customer_id === cust.customer_id)) return prev;
      return { ...prev, [industry]: [cust, ...current] };
    });
  };

  /* API Calls */
  const predictManual = async () => {
    setLoading(true);
    try {
      const numericForm = {};
      for (const [k, v] of Object.entries(form)) {
        const n = parseFloat(v);
        numericForm[k] = isNaN(n) ? v : n;
      }
      const res = await axios.post("http://localhost:8000/predict", { industry, customer_id: "CUST-MANUAL-001", data: numericForm });
      setSelectedCustomer(res.data); markInspected(res.data);
      setStrategyResult(null); navigate("customer_detail");
    } catch (err) { alert("Prediction failed: " + (err.response?.data?.detail || err.message)); }
    setLoading(false);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    if (fileInputRef.current) fileInputRef.current.value = "";
    const formData = new FormData();
    formData.append("file", file); formData.append("industry", industry);
    setUploadStatus("uploading"); setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/bulk_predict", formData, { headers: { "Content-Type": "multipart/form-data" } });
      setAllBulkResults((p) => ({ ...p, [industry]: res.data }));
      setSearchQuery(""); setRiskFilter("ALL"); setCurrentPage(1);
      setUploadStatus("success"); navigate("dashboard");
    } catch (err) { setUploadStatus("error"); alert("Bulk prediction failed: " + (err.response?.data?.detail || err.message)); }
    setLoading(false);
  };

  const fetchStrategy = async (cust) => {
    const target = cust || selectedCustomer; if (!target) return;
    markRetained(target);
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/strategy", {
        customer_id: target.customer_id, industry,
        risk_level: target.risk_level, churn_probability: target.churn_probability,
        top_drivers: target.top_drivers || target.top_churn_drivers || [],
        profile: target.profile || form
      });
      setStrategyResult(res.data);
    } catch (err) { console.error("Strategy fetch error:", err); }
    setLoading(false);
  };

  const generateComm = async () => {
    const activeCust = selectedCustomer; if (!activeCust) return;
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/communication/generate", {
        customer_id: activeCust.customer_id, industry,
        risk_level: activeCust.risk_level, churn_probability: activeCust.churn_probability,
        top_drivers: activeCust.top_drivers || activeCust.top_churn_drivers || [],
        recommendation: strategyResult?.recommendation || "Targeted retention engagement offer",
        channel: commChannel, tone: commTone, profile: activeCust.profile || activeCust
      });
      setCommResult(res.data);
    } catch (err) { alert("Communication generation failed: " + (err.response?.data?.detail || err.message)); }
    setLoading(false);
  };

  const inspectCustomer = (cust) => {
    setSelectedCustomer(cust); markInspected(cust);
    setStrategyResult(null); setCommResult(null); navigate("customer_detail");
  };

  const exportCSV = () => {
    if (!bulkResult) return;
    const headers = ["customer_id","churn_probability","risk_level","primary_exposure"];
    const rows = bulkResult.predictions.map((c) => {
      const primary = c.financial_exposure?.risk_revenue_loss ?? c.financial_exposure?.transaction_volume_at_risk ?? 0;
      return [c.customer_id, c.churn_probability, c.risk_level, primary];
    });
    const csv = [headers, ...rows].map((r) => r.map((v) => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `churnshield_${industry}_export.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  /* Filtered + Paginated Customers */
  const filteredCustomers = useMemo(() => {
    if (!bulkResult) return [];
    let list = [...bulkResult.predictions];
    if (riskFilter !== "ALL") list = list.filter((c) => c.risk_level === riskFilter);
    if (searchQuery.trim()) list = list.filter((c) => c.customer_id.toLowerCase().includes(searchQuery.toLowerCase()));
    if (sortBy === "churn_probability") list.sort((a, b) => b.churn_probability - a.churn_probability);
    else if (sortBy === "exposure") list.sort((a, b) => (b.financial_exposure?.risk_revenue_loss ?? 0) - (a.financial_exposure?.risk_revenue_loss ?? 0));
    else if (sortBy === "customer_id") list.sort((a, b) => a.customer_id.localeCompare(b.customer_id));
    return list;
  }, [bulkResult, riskFilter, searchQuery, sortBy]);

  const totalPages = Math.ceil(filteredCustomers.length / ITEMS_PER_PAGE);
  const paginatedCustomers = filteredCustomers.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  /* ════════════ RENDER ════════════ */
  return (
    <div className="cs-bg" style={{ position: "relative", minHeight: "100vh" }}>
      {/* Background Orbs */}
      <div className="cs-orb cs-orb-1" />
      <div className="cs-orb cs-orb-2" />
      <div className="cs-orb cs-orb-3" />

      {/* ── TOP NAV (hidden on landing) ── */}
      {page !== "industry" && (
        <nav className="cs-nav" style={{ position: "relative", zIndex: 50 }}>
          {/* Logo */}
          <div
            onClick={() => setPage("industry")}
            style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginRight: 24 }}
          >
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "linear-gradient(135deg, #4F46E5, #7C3AED)",
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <ShieldCheck size={16} color="#fff" />
            </div>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#111827", letterSpacing: "-0.3px" }}>
              ChurnShield
            </span>
          </div>

          {/* Nav Links */}
          {NAV_ITEMS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => navigate(id)}
              className={`cs-nav-link ${(page === id || (id === "customer_detail" && page === "customer_detail") || (id === "retention" && page === "retention")) ? "active" : ""}`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}

          <div style={{ flex: 1 }} />

          {/* AI Badge */}
          <div className="cs-ai-badge">
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#10B981", display: "inline-block" }} className="animate-pulse-dot" />
            AI Intelligence Active
          </div>

          {/* Domain pill */}
          <button
            onClick={() => setPage("industry")}
            style={{
              marginLeft: 12, padding: "6px 14px", borderRadius: 8,
              border: "1.5px solid var(--border)", background: "#fff",
              fontSize: 12, color: "var(--text-secondary)", cursor: "pointer",
              display: "flex", alignItems: "center", gap: 6, fontFamily: "Inter, sans-serif"
            }}
          >
            <currentMeta.Icon size={13} color="var(--primary)" />
            Selected Domain: {currentMeta.label}
          </button>
        </nav>
      )}

      {/* ── MAIN ── */}
      <main style={{ position: "relative", zIndex: 1, maxWidth: page === "industry" ? "none" : 1200, margin: "0 auto", padding: page === "industry" ? 0 : "32px 24px 48px" }}>

        {/* ══════════════════════════════
            PAGE 1 — LANDING (FULL SCREEN)
        ══════════════════════════════ */}
        {page === "industry" && (
          <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", width: "100%" }}>

            {/* ─── HERO SECTION ─── */}
            <div className="cs-hero-padding" style={{
              textAlign: "center",
              padding: "80px 64px 60px",
              position: "relative",
              flex: "0 0 auto",
              width: "100%",
              boxSizing: "border-box"
            }}>

              {/* Floating stat card — top left */}
              <div style={{ position: "absolute", top: 72, left: "5%", zIndex: 2 }} className="cs-stat-float cs-fade-up">
                <div style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500, marginBottom: 5 }}>Churn Probability</div>
                <div style={{ fontSize: 36, fontWeight: 800, color: "#EF4444", lineHeight: 1 }}>87%</div>
                <div style={{ fontSize: 11, color: "#EF4444", fontWeight: 700, marginTop: 3 }}>High Risk</div>
                <div style={{ height: 48, marginTop: 10, display: "flex", alignItems: "flex-end", gap: 3 }}>
                  {[18, 26, 16, 38, 30, 46, 40].map((h, i) => (
                    <div key={i} style={{ width: 8, height: h, borderRadius: 3, background: i === 6 ? "#EF4444" : `rgba(239,68,68,${0.15 + i * 0.1})` }} />
                  ))}
                </div>
                <div style={{ height: 40, marginTop: 10 }}>
                  <svg viewBox="0 0 120 40" width="120" height="40">
                    <polyline points="0,35 20,28 40,32 60,18 80,24 100,10 120,14" stroke="#EF4444" strokeWidth="2" fill="none" strokeLinecap="round" />
                  </svg>
                </div>
              </div>

              {/* Floating stat card — top right top */}
              <div style={{ position: "absolute", top: 72, right: "5%", zIndex: 2 }} className="cs-stat-float cs-fade-up-d1">
                <div style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500, marginBottom: 5 }}>Revenue at Risk</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: "#EF4444", lineHeight: 1 }}>$4.8M</div>
                <div style={{ height: 44, marginTop: 10 }}>
                  <svg viewBox="0 0 100 44" width="100" height="44" fill="none">
                    <polyline points="0,38 16,30 32,35 48,20 64,26 80,12 100,16" stroke="#EF4444" strokeWidth="2" fill="none" />
                    <polyline points="0,38 16,30 32,35 48,20 64,26 80,12 100,16 100,44 0,44" fill="rgba(239,68,68,0.07)" />
                  </svg>
                </div>
              </div>

              {/* Floating stat card — right, lower */}
              <div style={{ position: "absolute", top: 230, right: "5%", zIndex: 2 }} className="cs-stat-float cs-fade-up-d2">
                <div style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500, marginBottom: 5 }}>At Risk Customers</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: "#111827", lineHeight: 1 }}>2,341</div>
                <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap", maxWidth: 130 }}>
                  {Array(10).fill(0).map((_, i) => (
                    <div key={i} style={{ width: 16, height: 16, borderRadius: "50%", background: i < 6 ? "var(--primary)" : "#E5E7EB" }} />
                  ))}
                </div>
              </div>

              {/* Main title block */}
              <h1 className="cs-hero-title" style={{ fontSize: 64, fontWeight: 900, letterSpacing: "-2px", color: "#111827", marginBottom: 12, lineHeight: 1.05, fontFamily: "Inter, sans-serif" }}>
                CHURNSHIELD
              </h1>
              <h2 className="cs-hero-subtitle" style={{ fontSize: 26, fontWeight: 700, color: "var(--primary)", marginBottom: 20, letterSpacing: "-0.3px" }}>
                AI-Powered Customer Retention Intelligence
              </h2>
              <p style={{ fontSize: 17, color: "var(--text-secondary)", maxWidth: 560, margin: "0 auto 56px", lineHeight: 1.75 }}>
                Predict customer churn, understand customer risk, and take smarter retention actions.
              </p>

              {/* Domain selection header */}
              <h3 style={{ fontSize: 28, fontWeight: 800, color: "#111827", marginBottom: 10, letterSpacing: "-0.4px" }}>Select your business domain</h3>
              <p style={{ fontSize: 16, color: "var(--text-secondary)", marginBottom: 48 }}>
                Choose an industry to enter its dedicated customer intelligence workspace.
              </p>
            </div>

            {/* ─── INDUSTRY CARDS ─── */}
            <div className="cs-grid-3 cs-cards-padding" style={{
              maxWidth: 1280,
              width: "100%",
              margin: "0 auto",
              padding: "0 64px 80px",
              boxSizing: "border-box",
              flex: "0 0 auto"
            }}>
              {Object.entries(INDUSTRY_META).map(([key, meta]) => (
                <div key={key} className="cs-card cs-card-hover cs-fade-up" style={{ padding: 36, display: "flex", flexDirection: "column", gap: 22 }}>
                  {/* Icon */}
                  <div style={{ width: 56, height: 56, borderRadius: 14, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--primary)" }}>
                    <meta.Icon size={26} />
                  </div>

                  {/* Content */}
                  <div>
                    <h3 style={{ fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 10 }}>{meta.label}</h3>
                    <p style={{ fontSize: 14.5, color: "var(--text-secondary)", lineHeight: 1.65 }}>{meta.desc}</p>
                  </div>

                  {/* Tags */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {meta.tags.map((tag, i) => (
                      <span key={tag} className={`cs-tag ${meta.tagStyles[i]}`} style={{ fontSize: 12 }}>{tag}</span>
                    ))}
                  </div>

                  {/* CTA */}
                  <button className="cs-industry-btn" style={{ padding: "14px 24px", fontSize: 14 }} onClick={() => selectIndustry(key)}>
                    Enter {meta.label.split(" ")[0]} <ArrowRight size={16} />
                  </button>
                </div>
              ))}
            </div>

            {/* ─── WHY CHURNSHIELD SECTION ─── */}
            <div style={{
              background: "rgba(255,255,255,0.65)",
              borderTop: "1px solid var(--border)",
              padding: "72px 64px 80px",
              textAlign: "center",
              width: "100%",
              boxSizing: "border-box",
              flex: "1 0 auto"
            }}>
              <h2 style={{ fontSize: 34, fontWeight: 800, color: "#111827", marginBottom: 10, letterSpacing: "-0.5px" }}>Why ChurnShield?</h2>
              <p style={{ fontSize: 17, color: "var(--text-secondary)", marginBottom: 60 }}>One platform. Smarter retention. Measurable impact.</p>
              <div className="cs-grid-5" style={{ maxWidth: 1280, margin: "0 auto" }}>
                {[
                  { Icon: BrainCircuit, title: "AI-Powered Prediction", desc: "Advanced ML models predict churn risk with high accuracy." },
                  { Icon: Target, title: "Risk Insights", desc: "Understand why customers are at risk with explainable AI." },
                  { Icon: Lightbulb, title: "Smart Recommendations", desc: "Get action-driven retention strategies tailored to each customer." },
                  { Icon: MessageSquare, title: "Personalized Outreach", desc: "Generate personalized communications that drive engagement." },
                  { Icon: TrendingUp, title: "Business Impact", desc: "Reduce churn, increase LTV, and grow your revenue." },
                ].map(({ Icon, title, desc }) => (
                  <div key={title} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
                    <div style={{
                      width: 72, height: 72, borderRadius: 18, background: "#EEF2FF",
                      display: "flex", alignItems: "center", justifyContent: "center", color: "var(--primary)",
                      boxShadow: "0 4px 14px rgba(99,102,241,0.12)"
                    }}>
                      <Icon size={30} />
                    </div>
                    <div style={{ fontWeight: 700, fontSize: 15, color: "#111827" }}>{title}</div>
                    <div style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.65 }}>{desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════
            PAGE 2 — DATA INPUT
        ══════════════════════════════ */}
        {page === "input" && (
          <div style={{ maxWidth: 960, margin: "0 auto" }}>
            {/* Breadcrumb */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-secondary)", marginBottom: 20 }}>
              <span style={{ cursor: "pointer" }} onClick={() => setPage("industry")}>Workspace</span>
              <ChevronRight size={12} />
              <span>Data Ingestion</span>
              <ChevronRight size={12} />
              <span style={{ color: "var(--primary)", fontWeight: 600 }}>New Dataset</span>
            </div>

            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 28 }}>
              <div>
                <h1 style={{ fontSize: 28, fontWeight: 800, color: "#111827", marginBottom: 8, letterSpacing: "-0.5px" }}>Data Input</h1>
                <p style={{ fontSize: 13.5, color: "var(--text-secondary)", maxWidth: 480, lineHeight: 1.6 }}>
                  Upload batch historical data or manually input single records for immediate AI risk assessment.
                </p>
              </div>
              <div style={{
                display: "flex", alignItems: "center", gap: 8,
                border: "1.5px solid var(--border)", background: "#fff",
                borderRadius: 20, padding: "8px 16px", fontSize: 13, fontWeight: 600, color: "var(--primary)"
              }}>
                <currentMeta.Icon size={14} />
                Selected Domain: {currentMeta.label}
                <button style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0, display: "flex" }}>
                  <FileText size={13} />
                </button>
              </div>
            </div>

            {/* Two-column grid */}
            <div className="cs-grid-2">
              {/* Bulk CSV Upload */}
              <div>
                <div className="cs-card" style={{ padding: 28 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                    <div className="cs-icon-box-sm" style={{ background: "#EEF2FF" }}><Upload size={16} /></div>
                    <h3 style={{ fontSize: 17, fontWeight: 700, color: "#111827" }}>Bulk CSV Upload</h3>
                  </div>

                  {/* Dropzone */}
                  <label className="cs-dropzone" style={{ display: "block", cursor: "pointer" }}>
                    <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileUpload} style={{ display: "none" }} />
                    <Upload size={32} color="#9CA3AF" style={{ margin: "0 auto 12px" }} />
                    <div style={{ fontSize: 13.5, color: "var(--text-secondary)", marginBottom: 6 }}>
                      Drag and drop your dataset here
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>or</div>
                    <button
                      type="button"
                      style={{
                        background: "#fff", border: "1.5px solid var(--border)", borderRadius: 8,
                        padding: "8px 20px", fontSize: 13, fontWeight: 600, color: "#111827", cursor: "pointer"
                      }}
                    >Browse Files</button>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 10 }}>Supported format: .csv (Max 50MB)</div>
                  </label>

                  {/* Status indicators */}
                  {uploadStatus === "uploading" && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", borderRadius: 8, background: "#EEF2FF", border: "1px solid #C7D2FE", marginTop: 16, fontSize: 12, color: "var(--primary)" }}>
                      <RefreshCw size={14} className="spin-slow" /> Processing dataset...
                    </div>
                  )}
                  {uploadStatus === "success" && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", borderRadius: 8, background: "#F0FDF4", border: "1px solid #BBF7D0", marginTop: 16, fontSize: 12, color: "#15803D" }}>
                      <CheckCircle2 size={14} /> {bulkResult?.total_customers} customers processed
                    </div>
                  )}
                  {uploadStatus === "error" && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", borderRadius: 8, background: "#FEF2F2", border: "1px solid #FECACA", marginTop: 16, fontSize: 12, color: "#DC2626" }}>
                      <AlertTriangle size={14} /> Upload failed — check CSV format
                    </div>
                  )}

                  {/* Schema info */}
                  <div style={{ marginTop: 20, borderRadius: 10, border: "1px solid var(--border)", overflow: "hidden" }}>
                    {[["Schema Auto-Detection", "#10B981", "Ready"], ["AI Pre-processing", "#9CA3AF", "Standby"]].map(([label, color, status]) => (
                      <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderBottom: "1px solid var(--border-light)", background: "#FAFAFE" }}>
                        <span style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{label}</span>
                        <span style={{ fontSize: 11, fontWeight: 600, color, background: color + "15", padding: "2px 10px", borderRadius: 20, border: `1px solid ${color}30` }}>{status}</span>
                      </div>
                    ))}
                  </div>

                  <button
                    className="cs-btn-primary"
                    style={{ width: "100%", justifyContent: "center", marginTop: 20, padding: "13px 20px", borderRadius: 10, fontSize: 14 }}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading && uploadStatus === "uploading"}
                  >
                    <Sparkles size={15} />
                    {loading && uploadStatus === "uploading" ? "Processing..." : "Process Dataset"}
                  </button>
                </div>

                {/* Formatting Tips */}
                <div className="cs-card" style={{ padding: 16, marginTop: 16, display: "flex", gap: 12, alignItems: "flex-start" }}>
                  <Lightbulb size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#111827", marginBottom: 4 }}>Formatting Tips</div>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                      Ensure your CSV includes columns for <em>Customer_ID</em>, <em>Tenure</em>, and <em>Monthly_Charges</em> for optimal risk prediction accuracy.
                    </div>
                  </div>
                </div>
              </div>

              {/* Manual Customer Input */}
              <div className="cs-card" style={{ padding: 28, display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div className="cs-icon-box-sm"><UserRound size={16} /></div>
                    <h3 style={{ fontSize: 17, fontWeight: 700, color: "#111827" }}>Manual Customer Input</h3>
                  </div>
                  <button
                    onClick={() => setForm(DOMAIN_DEFAULTS[industry] || {})}
                    style={{ fontSize: 12, color: "var(--primary)", background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}
                  >Clear Form</button>
                </div>

                {/* Form fields — 2 column grid */}
                <div style={{ flex: 1, overflowY: "auto", maxHeight: 380 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                    {DOMAIN_FIELDS[industry].slice(0, 8).map((field) => (
                      <div key={field.key}>
                        <label style={{ fontSize: 11.5, color: "var(--text-secondary)", fontWeight: 500, display: "block", marginBottom: 5 }}>
                          {field.label} {field.key === "Customer ID" && <span style={{ color: "#EF4444" }}>*</span>}
                        </label>
                        {field.type === "select" ? (
                          <select
                            className="cs-select"
                            style={{ width: "100%" }}
                            value={form[field.key] ?? ""}
                            onChange={(e) => setForm((p) => ({ ...p, [field.key]: e.target.value }))}
                          >
                            {field.options.map((opt, i) => (
                              <option key={opt} value={opt}>{field.labels ? field.labels[i] : opt}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="number"
                            className="cs-input"
                            min={field.min} max={field.max} step={field.step || 1}
                            value={form[field.key] ?? ""}
                            onChange={(e) => setForm((p) => ({ ...p, [field.key]: e.target.value }))}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer buttons */}
                <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
                  <button className="cs-btn-secondary" style={{ flex: 1, justifyContent: "center" }}>
                    Save as Draft
                  </button>
                  <button
                    className="cs-btn-primary"
                    style={{ flex: 2, justifyContent: "center", padding: "12px 24px", borderRadius: 10 }}
                    onClick={predictManual}
                    disabled={loading}
                  >
                    <Zap size={15} />
                    {loading ? "Assessing..." : "Assess Risk →"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════
            PAGE 3 — DASHBOARD
        ══════════════════════════════ */}
        {page === "dashboard" && (
          <div>
            {!bulkResult ? (
              /* Empty State */
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 480, gap: 20, textAlign: "center" }}>
                <div style={{ width: 72, height: 72, borderRadius: 20, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <LayoutDashboard size={32} color="var(--primary)" />
                </div>
                <div>
                  <h3 style={{ fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 8 }}>No Data Loaded</h3>
                  <p style={{ fontSize: 14, color: "var(--text-secondary)", maxWidth: 360 }}>Upload a CSV dataset to populate your executive analytics dashboard.</p>
                </div>
                <button className="cs-btn-primary" onClick={() => navigate("input")}>
                  <Upload size={15} /> Go to Data Input
                </button>
              </div>
            ) : (
              <div>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 28 }}>
                  <div>
                    <h1 style={{ fontSize: 26, fontWeight: 800, color: "#111827", marginBottom: 4, letterSpacing: "-0.4px" }}>Executive Overview</h1>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>Real-time analysis of customer retention and risk factors.</p>
                  </div>
                  <button className="cs-btn-primary" onClick={exportCSV} style={{ gap: 8 }}>
                    <Download size={14} /> Export Report
                  </button>
                </div>

                {/* KPI Cards */}
                <div className="cs-grid-4" style={{ marginBottom: 24 }}>
                  {[
                    { label: "Total Customers", value: bulkResult.total_customers?.toLocaleString(), delta: "+2.4%", Icon: Users, color: "var(--primary)", isRisk: false },
                    { label: "High Risk Customers", value: (bulkResult.risk_summary?.HIGH || 0) + (bulkResult.risk_summary?.CRITICAL || 0), delta: `+${bulkResult.risk_summary?.CRITICAL || 0}`, Icon: AlertTriangle, color: "#EF4444", isRisk: true },
                    { label: "Avg Churn Probability", value: `${((bulkResult.average_churn_probability || 0) * 100).toFixed(0)}%`, delta: "— 0%", Icon: Activity, color: "#8B5CF6", isRisk: false },
                    currentMeta.hasRevenueRisk
                      ? { label: "Revenue at Risk (30d)", value: `$${((bulkResult.total_portfolio_financial_exposure || 0) / 1000).toFixed(1)}k`, delta: "", Icon: BarChart2, color: "#6366F1", isRisk: false }
                      : { label: "At-Risk Accounts", value: bulkResult.customers_at_risk?.toLocaleString(), delta: "", Icon: BarChart2, color: "#6366F1", isRisk: false }
                  ].map((kpi, i) => {
                    const KpiIcon = kpi.Icon;
                    return (
                      <div key={i} className="cs-card" style={{ padding: 20, borderTop: kpi.isRisk ? "2px solid #EF4444" : "2px solid transparent" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                          <KpiIcon size={16} color={kpi.color} />
                          {kpi.delta && <span style={{ fontSize: 11, color: "#10B981", fontWeight: 600 }}>↑ {kpi.delta}</span>}
                        </div>
                        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 4 }}>{kpi.label}</div>
                        <div style={{ fontSize: 28, fontWeight: 800, color: "#111827", letterSpacing: "-0.5px" }}>{kpi.value}</div>
                      </div>
                    );
                  })}
                </div>

                {/* Charts Row */}
                <div className="cs-grid-2" style={{ marginBottom: 24 }}>
                  {/* Risk Distribution */}
                  <div className="cs-card" style={{ padding: 24 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, color: "#111827" }}>Risk Distribution</h3>
                      <span style={{ fontSize: 18, cursor: "pointer", color: "var(--text-muted)" }}>⋮</span>
                    </div>
                    <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
                      <div style={{ width: 140, height: 140 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={[
                                { name: "Low", value: bulkResult.risk_summary?.LOW || 0 },
                                { name: "Medium", value: bulkResult.risk_summary?.MEDIUM || 0 },
                                { name: "High+Critical", value: (bulkResult.risk_summary?.HIGH || 0) + (bulkResult.risk_summary?.CRITICAL || 0) },
                              ]}
                              cx="50%" cy="50%" innerRadius={42} outerRadius={68} dataKey="value" paddingAngle={3}
                            >
                              {["#10B981", "#8B5CF6", "#EF4444"].map((color, i) => (
                                <Cell key={i} fill={color} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 8, fontSize: 12 }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 26, fontWeight: 800, color: "#111827" }}>
                          {(bulkResult.risk_summary?.HIGH || 0) + (bulkResult.risk_summary?.CRITICAL || 0)}
                        </div>
                        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>High Risk</div>
                        {[["Low", "var(--risk-low)"], ["Medium", "var(--risk-medium)"], ["High", "var(--risk-critical)"]].map(([label, color]) => (
                          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                            <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
                            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Probability Curve */}
                  <div className="cs-card" style={{ padding: 24 }}>
                    <div style={{ marginBottom: 4 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, color: "#111827", marginBottom: 2 }}>Probability Curve</h3>
                      <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Distribution of customer churn scores</div>
                    </div>
                    <div style={{ height: 160, marginTop: 16 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={(() => {
                            const buckets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                            (bulkResult.predictions || []).forEach((c) => {
                              const idx = Math.min(9, Math.floor(c.churn_probability * 10));
                              buckets[idx]++;
                            });
                            return buckets.map((v, i) => ({ label: `${i * 10}%`, count: v }));
                          })()}
                          margin={{ top: 4, right: 4, left: -24, bottom: 0 }}
                        >
                          <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#9CA3AF" }} />
                          <YAxis tick={{ fontSize: 10, fill: "#9CA3AF" }} />
                          <Bar dataKey="count" fill="#6366F1" radius={[3, 3, 0, 0]} />
                          <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 8, fontSize: 12 }} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Customers at Risk Table */}
                <div className="cs-card" style={{ overflow: "hidden" }}>
                  <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: "#111827", marginBottom: 3 }}>Customers at Risk</h3>
                      <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>Top priority accounts requiring intervention</p>
                    </div>
                    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <div style={{ position: "relative" }}>
                        <Search size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                        <input
                          className="cs-input"
                          style={{ paddingLeft: 30, width: 160, padding: "8px 12px 8px 28px" }}
                          placeholder="Search ID..."
                          value={searchQuery}
                          onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                        />
                      </div>
                      {/* Filter */}
                      <div style={{ display: "flex", background: "#F9FAFB", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
                        {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((level) => (
                          <button
                            key={level}
                            onClick={() => { setRiskFilter(level); setCurrentPage(1); }}
                            style={{
                              padding: "6px 12px", fontSize: 11, fontWeight: 600, border: "none", cursor: "pointer",
                              background: riskFilter === level ? "var(--primary)" : "transparent",
                              color: riskFilter === level ? "#fff" : "var(--text-secondary)",
                              transition: "all 0.15s"
                            }}
                          >{level}</button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="cs-table-wrapper">
                    <table className="cs-table">
                      <thead>
                        <tr>
                          <th>Customer ID</th>
                          <th>Industry / Domain</th>
                          <th>Risk Level</th>
                          <th>Churn Probability</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedCustomers.map((cust) => {
                          const pct = Math.round(cust.churn_probability * 100);
                          const fgColors = { CRITICAL: "#EF4444", HIGH: "#F97316", MEDIUM: "#8B5CF6", LOW: "#10B981" };

                          return (
                            <tr key={cust.customer_id}>
                              <td>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                  <div style={{
                                    width: 32, height: 32, borderRadius: 8, background: "#EEF2FF",
                                    display: "flex", alignItems: "center", justifyContent: "center"
                                  }}>
                                    <User size={14} color="var(--primary)" />
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 600, fontSize: 13, color: "#111827" }}>{cust.customer_id}</div>
                                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ID: {cust.customer_id}</div>
                                  </div>
                                </div>
                              </td>
                              <td><span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{currentMeta.label}</span></td>
                              <td><RiskBadge level={cust.risk_level} /></td>
                              <td>
                                <span style={{ fontSize: 14, fontWeight: 700, color: fgColors[cust.risk_level] || "var(--primary)" }}>
                                  {pct}%
                                </span>
                              </td>
                              <td>
                                <button
                                  onClick={() => inspectCustomer(cust)}
                                  className="cs-btn-primary"
                                  style={{ padding: "6px 14px", fontSize: 12, borderRadius: 8, display: "inline-flex", alignItems: "center", gap: 5 }}
                                >
                                  <Eye size={13} /> Inspect
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div style={{ padding: "14px 24px", borderTop: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                      Showing {Math.min(1, filteredCustomers.length)}-{Math.min(currentPage * ITEMS_PER_PAGE, filteredCustomers.length)} of {filteredCustomers.length} at risk
                    </span>
                    <div style={{ display: "flex", gap: 4 }}>
                      <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} className="cs-btn-ghost" style={{ padding: "4px 8px" }}>
                        <ChevronLeft size={14} />
                      </button>
                      <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} className="cs-btn-ghost" style={{ padding: "4px 8px" }}>
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════
            PAGE 4 — CUSTOMER DETAIL
        ══════════════════════════════ */}
        {page === "customer_detail" && selectedCustomer && (() => {
          const prob = Math.round(selectedCustomer.churn_probability * 100);
          const riskColor = { CRITICAL: "#EF4444", HIGH: "#F97316", MEDIUM: "#8B5CF6", LOW: "#10B981" }[selectedCustomer.risk_level] || "#8B5CF6";
          const drivers = selectedCustomer.top_drivers || selectedCustomer.top_churn_drivers || [];
          const maxAbs = Math.max(...drivers.map((d) => Math.abs(d.impact ?? 0)), 0.01);
          const primaryLoss = selectedCustomer.financial_exposure?.risk_revenue_loss ?? selectedCustomer.financial_exposure?.transaction_volume_at_risk ?? 0;

          return (
            <div>
              {/* Back nav */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
                <button onClick={goBack} className="cs-btn-ghost" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                  <ChevronLeft size={15} /> Back to Dashboard
                </button>
                <div className="cs-ai-badge">
                  <BrainCircuit size={13} /> AI Intelligence Active
                </div>
              </div>

              {/* Customer Header */}
              <div style={{ marginBottom: 28 }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>
                      CUSTOMER PROFILE
                      <span style={{ marginLeft: 10 }}>
                        <RiskBadge level={selectedCustomer.risk_level} />
                      </span>
                    </div>
                    <h1 style={{ fontSize: 42, fontWeight: 900, color: "#111827", letterSpacing: "-1px", marginBottom: 8, fontFamily: "Inter, sans-serif" }}>
                      {selectedCustomer.customer_id}
                    </h1>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                      {currentMeta.label} Sector • Active account
                    </p>
                  </div>
                  {/* Churn prob box */}
                  <div className="cs-card" style={{ padding: "16px 24px", textAlign: "right", minWidth: 140 }}>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 4 }}>Churn Probability</div>
                    <div style={{ fontSize: 32, fontWeight: 800, color: riskColor }}>
                      {prob}% <span style={{ fontSize: 18 }}>↗</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Main 2-column layout */}
              <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 24, marginBottom: 24 }}>
                {/* Left: Profile Card */}
                <div>
                  <div className="cs-card" style={{ padding: 24 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                      <div style={{ width: 40, height: 40, borderRadius: 10, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Building2 size={18} color="var(--primary)" />
                      </div>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>Customer Account</div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ID: {selectedCustomer.customer_id}</div>
                      </div>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12 }}>DOMAIN METRICS</div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {Object.entries(selectedCustomer.profile || {}).slice(0, 6).map(([k, v]) => (
                          v !== null && v !== undefined && (
                            <div key={k} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <FileText size={12} color="var(--text-muted)" />
                                <span style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{k.replace(/_/g, " ")}</span>
                              </div>
                              <span style={{ fontSize: 12.5, fontWeight: 600, color: "#111827" }}>{String(v)}</span>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: SHAP Analysis */}
                <div className="cs-card" style={{ padding: 28 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                    <div>
                      <h3 style={{ fontSize: 17, fontWeight: 700, color: "#111827", marginBottom: 4 }}>Why is this customer likely to churn?</h3>
                      <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.5, maxWidth: 480 }}>
                        Our intelligence engine has identified the key factors driving this account's churn probability. Values leaning right (red) push the score towards churn, while values leaning left (green) reduce risk.
                      </p>
                    </div>
                    <button className="cs-btn-secondary" style={{ fontSize: 11, padding: "6px 12px", borderRadius: 8, whiteSpace: "nowrap" }}>
                      SHAP Value Analysis
                    </button>
                  </div>

                  {/* SHAP Bars */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {drivers.slice(0, 6).map((driver, idx) => {
                      const val = driver.impact ?? 0;
                      const isPositive = val > 0;
                      const absVal = Math.abs(val);
                      const normWidth = Math.min((absVal / maxAbs) * 44, 44);
                      const featVal = driver.feature_value;
                      const featLabel = driver.feature || `Feature ${idx + 1}`;
                      const importance = driver.importance;

                      return (
                        <div key={idx} style={{ display: "flex", alignItems: "center", gap: 16 }}>
                          {/* Feature name + value */}
                          <div style={{ width: 200, flexShrink: 0 }}>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: "#111827", marginBottom: 2 }}>
                              {featLabel}{featVal !== null && featVal !== undefined ? `: ${String(featVal)}` : ""}
                            </div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                              {isPositive ? "Increases churn risk" : "Historical loyalty"}
                              {importance ? ` • ${importance.toFixed(1)}%` : ""}
                            </div>
                          </div>

                          {/* Bar */}
                          <div style={{ flex: 1, position: "relative", height: 28, background: "#F9FAFB", borderRadius: 6, overflow: "visible", border: "1px solid var(--border-light)", display: "flex", alignItems: "center" }}>
                            {/* Center axis */}
                            <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1.5, background: "rgba(107,114,128,0.25)", zIndex: 2 }} />
                            {/* SHAP value label IN bar */}
                            {isPositive ? (
                              <div style={{
                                position: "absolute", left: "50%", top: "50%", transform: "translateY(-50%)",
                                width: `${normWidth}%`, height: 20, borderRadius: "0 4px 4px 0",
                                background: "#EF4444", display: "flex", alignItems: "center", justifyContent: "center"
                              }}>
                                <span style={{ fontSize: 10, fontWeight: 700, color: "#fff", whiteSpace: "nowrap", paddingLeft: 4 }}>+{val.toFixed(2)}</span>
                              </div>
                            ) : (
                              <div style={{
                                position: "absolute", right: "50%", top: "50%", transform: "translateY(-50%)",
                                width: `${normWidth}%`, height: 20, borderRadius: "4px 0 0 4px",
                                background: "#10B981", display: "flex", alignItems: "center", justifyContent: "center"
                              }}>
                                <span style={{ fontSize: 10, fontWeight: 700, color: "#fff", whiteSpace: "nowrap", paddingRight: 4 }}>{val.toFixed(2)}</span>
                              </div>
                            )}
                          </div>

                          {/* Direction badge */}
                          <span className={isPositive ? "badge-shap-risk" : "badge-shap-protect"} style={{ flexShrink: 0, fontSize: 9, fontWeight: 700 }}>
                            {isPositive ? "▲ RISK" : "▼ SAFE"}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* AI Strategic Insight */}
                  {(selectedCustomer.strategy_summary || selectedCustomer.recommendation) && (
                    <div style={{ marginTop: 24, padding: 16, borderRadius: 12, background: "#FAFAFE", border: "1px solid #E0E7FF" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                        <Lightbulb size={15} color="var(--primary)" />
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--primary)" }}>AI Strategic Insight</span>
                      </div>
                      <p style={{ fontSize: 12.5, color: "#374151", lineHeight: 1.65 }}>
                        {selectedCustomer.strategy_summary || selectedCustomer.recommendation}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer Action Bar */}
              <div className="cs-card" style={{ padding: "18px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: "#FEF2F2", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <TrendingDown size={18} color="#EF4444" />
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>REVENUE AT RISK</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: "#111827" }}>
                      ${primaryLoss.toLocaleString()} <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)" }}>/ Annualized</span>
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                  <button className="cs-btn-secondary" style={{ fontSize: 13 }}>Log Activity</button>
                  <button
                    className="cs-btn-primary"
                    style={{ fontSize: 13, padding: "10px 24px", borderRadius: 10 }}
                    onClick={() => { fetchStrategy(selectedCustomer); navigate("retention"); }}
                  >
                    Retain Customer →
                  </button>
                </div>
              </div>
            </div>
          );
        })()}

        {/* ══════════════════════════════
            PAGE 5 — CUSTOMER PORTFOLIO
        ══════════════════════════════ */}
        {(page === "customer_portfolio" || page === "customer_intelligence") && (
          <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 28 }}>
              <div>
                <h1 style={{ fontSize: 26, fontWeight: 800, color: "#111827", marginBottom: 6, letterSpacing: "-0.4px" }}>Customer Portfolio</h1>
                <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  Portfolio of accounts with active retention strategies ({retainedCustomers.length} retained)
                </p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#EEF2FF", border: "1px solid #C7D2FE", borderRadius: 20, padding: "6px 14px", fontSize: 12, fontWeight: 600, color: "var(--primary)" }}>
                <ShieldCheck size={14} />
                {retainedCustomers.length} Retained Accounts
              </div>
            </div>

            {retainedCustomers.length === 0 ? (
              <div className="cs-card" style={{ padding: "56px 32px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
                <div style={{ width: 64, height: 64, borderRadius: 18, background: "#EEF2FF", border: "1px solid #C7D2FE", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <ShieldCheck size={32} color="var(--primary)" />
                </div>
                <div>
                  <h3 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 8 }}>No Retained Customers Yet</h3>
                  <p style={{ fontSize: 13.5, color: "var(--text-secondary)", maxWidth: 460, lineHeight: 1.6, margin: "0 auto" }}>
                    Click <strong>Inspect</strong> on any customer from your Dashboard, then click <strong>Retain Customer</strong> to generate an AI retention strategy and add them to your portfolio.
                  </p>
                </div>
                <button className="cs-btn-primary" style={{ marginTop: 8 }} onClick={() => navigate("dashboard")}>
                  <LayoutDashboard size={15} /> Go to Dashboard
                </button>
              </div>
            ) : (
              <div>
                {/* Customer grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                  {retainedCustomers.map((cust) => {
                    const prob = Math.round((cust.churn_probability || 0) * 100);
                    const riskColor = RISK_COLORS[cust.risk_level] || "#8B5CF6";
                    const topDriver = (cust.top_drivers?.[0] || cust.top_churn_drivers?.[0]);

                    return (
                      <div key={cust.customer_id} className="cs-card cs-card-hover" style={{ padding: 20 }}>
                        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 14 }}>
                          <div>
                            <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>{cust.customer_id}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{currentMeta.label}</div>
                          </div>
                          <RiskBadge level={cust.risk_level} />
                        </div>

                        {/* Status Chip */}
                        <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "3px 10px", borderRadius: 20, background: "#F0FDF4", border: "1px solid #BBF7D0", fontSize: 11, fontWeight: 600, color: "#16A34A", marginBottom: 14 }}>
                          <CheckCircle2 size={12} /> Retained in Portfolio
                        </div>

                        {/* Churn meter */}
                        <div style={{ marginBottom: 14 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                            <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Initial Churn Prob</span>
                            <span style={{ fontSize: 14, fontWeight: 800, color: riskColor }}>{prob}%</span>
                          </div>
                          <div className="churn-meter-track">
                            <div className="churn-meter-fill" style={{ width: `${prob}%`, background: riskColor }} />
                          </div>
                        </div>

                        {topDriver && (
                          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 14, padding: "6px 10px", background: "#F9FAFB", borderRadius: 6, border: "1px solid var(--border-light)" }}>
                            Primary Driver: <span style={{ fontWeight: 600, color: "#374151" }}>{topDriver.feature}</span>
                          </div>
                        )}

                        <div style={{ display: "flex", gap: 8 }}>
                          <button
                            className="cs-btn-secondary"
                            style={{ flex: 1, justifyContent: "center", fontSize: 12, padding: "8px" }}
                            onClick={() => inspectCustomer(cust)}
                          >
                            <Eye size={13} /> Inspect
                          </button>
                          <button
                            className="cs-btn-primary"
                            style={{ flex: 1, justifyContent: "center", fontSize: 12, padding: "8px" }}
                            onClick={() => { setSelectedCustomer(cust); fetchStrategy(cust); navigate("retention"); }}
                          >
                            <Shield size={13} /> Strategy
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════
            PAGE 6 — RETENTION STRATEGY
        ══════════════════════════════ */}
        {page === "retention" && (
          <div>
            {/* Back */}
            <button onClick={goBack} className="cs-btn-ghost" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, marginBottom: 24 }}>
              <ChevronLeft size={15} /> Back to Dashboard
            </button>

            {selectedCustomer && (
              <>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                      <h1 style={{ fontSize: 24, fontWeight: 800, color: "#111827", letterSpacing: "-0.4px" }}>Retention Strategy</h1>
                      <span style={{
                        padding: "4px 12px", borderRadius: 20, background: "#FEF2F2", border: "1px solid #FECACA",
                        fontSize: 12, fontWeight: 700, color: "#DC2626", display: "flex", alignItems: "center", gap: 4
                      }}>
                        ⚠ {Math.round((selectedCustomer.churn_probability || 0) * 100)}% Churn Prob
                      </span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "var(--text-secondary)" }}>
                      <span style={{ background: "#EEF2FF", color: "var(--primary)", padding: "2px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600 }}>
                        {selectedCustomer.customer_id}
                      </span>
                      <span>•</span>
                      <span>{currentMeta.label}</span>
                      <span>•</span>
                      <span>Active account</span>
                    </div>
                  </div>
                </div>

                {/* Main Grid */}
                <div className="cs-responsive-split">
                  {/* Left: Strategy */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {/* AI Recommended Approach */}
                    <div className="cs-card" style={{ padding: 28 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
                        <div style={{ width: 44, height: 44, borderRadius: 12, background: "linear-gradient(135deg, #EEF2FF, #DDD6FE)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <Sparkles size={20} color="var(--primary)" />
                        </div>
                        <div>
                          <h3 style={{ fontSize: 17, fontWeight: 700, color: "#111827", marginBottom: 2 }}>AI Recommended Approach</h3>
                          <p style={{ fontSize: 11.5, color: "var(--text-secondary)" }}>Clear step-by-step guidance tailored for this account</p>
                        </div>
                      </div>

                      {loading && !strategyResult ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 16, background: "#EEF2FF", borderRadius: 10, fontSize: 13, color: "var(--primary)" }}>
                          <RefreshCw size={15} className="spin-slow" /> Gemini AI is generating strategy...
                        </div>
                      ) : (
                        <>
                          {/* 3 to 4 lines simple explanation */}
                          <div style={{ background: "#FAFAFE", border: "1px solid #E0E7FF", borderRadius: 12, padding: 18, marginBottom: 20 }}>
                            <p style={{ fontSize: 13.5, color: "#374151", lineHeight: 1.7, margin: 0 }}>
                              {strategyResult?.summary || selectedCustomer?.strategy_summary || "This customer shows risk of leaving due to recent usage changes and cost concerns. Offering a targeted bill discount along with proactive support directly addresses their key dissatisfaction points. Reaching out with a clear benefit plan will quickly rebuild trust and keep them active on their account."}
                            </p>
                          </div>

                          {/* Metrics */}
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
                            <div style={{ padding: "14px 16px", background: "#F9FAFB", borderRadius: 10, border: "1px solid var(--border-light)" }}>
                              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 6 }}>EST. RETENTION BOOST</div>
                              <div style={{ fontSize: 24, fontWeight: 800, color: "var(--primary)" }}>+45% ↗</div>
                            </div>
                            <div style={{ padding: "14px 16px", background: "#F9FAFB", borderRadius: 10, border: "1px solid var(--border-light)" }}>
                              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 6 }}>REVENUE SAVED (ARR)</div>
                              <div style={{ fontSize: 24, fontWeight: 800, color: "#10B981" }}>
                                ${((selectedCustomer.financial_exposure?.risk_revenue_loss ?? 0) / 1000).toFixed(1)}k
                                <span style={{ fontSize: 13, fontWeight: 400, color: "var(--text-secondary)" }}>/mo</span>
                              </div>
                            </div>
                          </div>
                        </>
                      )}

                      {!strategyResult && !loading && (
                        <button
                          className="cs-btn-primary"
                          style={{ width: "100%", justifyContent: "center", padding: "12px", borderRadius: 10 }}
                          onClick={() => fetchStrategy(selectedCustomer)}
                        >
                          <Sparkles size={15} /> Generate AI Strategy
                        </button>
                      )}
                    </div>

                    {/* Strategy Components with Descriptions */}
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: "#111827", marginBottom: 16 }}>Strategy Components</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                        {[
                          {
                            title: "Service Recovery",
                            IconComp: Shield,
                            action: (strategyResult?.action_items?.[0] || selectedCustomer?.action_items?.[0] || "Address primary churn driver with targeted support"),
                            desc: "Fix support or technical issues immediately. Quick response restores confidence and prevents customer frustration."
                          },
                          {
                            title: "Targeted Discount",
                            IconComp: Target,
                            action: (strategyResult?.action_items?.[1] || selectedCustomer?.action_items?.[1] || "Apply custom bill adjustment offer"),
                            desc: "Offer a temporary price adjustment or bill credit. Reduces financial friction while keeping the customer active."
                          },
                          {
                            title: "Plan Upgrade",
                            IconComp: TrendingUp,
                            action: (strategyResult?.action_items?.[2] || selectedCustomer?.action_items?.[2] || "Upgrade to premium tier feature access"),
                            desc: "Provide extra feature access or subscription perks. Increasing value makes the service essential for daily needs."
                          },
                          {
                            title: "Loyalty Benefit",
                            IconComp: Star,
                            action: (strategyResult?.action_items?.[3] || selectedCustomer?.action_items?.[3] || "Enroll in priority customer rewards"),
                            desc: "Grant exclusive rewards or priority customer service. Feeling valued builds long-term brand loyalty."
                          }
                        ].map(({ title, IconComp, action, desc }, i) => (
                          <div key={i} className="cs-card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 8 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                              <div style={{ width: 34, height: 34, borderRadius: 8, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                <IconComp size={16} color="var(--primary)" />
                              </div>
                              <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>{title}</div>
                            </div>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: "var(--primary)", lineHeight: 1.4 }}>
                              {action}
                            </div>
                            <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55 }}>
                              {desc}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right: Customer Communication */}
                  <div className="cs-card" style={{ padding: 24, display: "flex", flexDirection: "column" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <Mail size={16} color="var(--primary)" />
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#111827" }}>Customer Communication</h3>
                      </div>
                      <button className="cs-btn-ghost" style={{ padding: "4px 8px" }} onClick={generateComm} title="Regenerate message">
                        <RefreshCw size={14} />
                      </button>
                    </div>

                    {/* Channel tabs */}
                    <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
                      {["email", "sms", "whatsapp", "call_script"].map((ch) => (
                        <button
                          key={ch}
                          onClick={() => setCommChannel(ch)}
                          style={{
                            padding: "5px 12px", fontSize: 11, fontWeight: 600, borderRadius: 6, border: "none",
                            cursor: "pointer", background: commChannel === ch ? "var(--primary)" : "#F3F4F6",
                            color: commChannel === ch ? "#fff" : "var(--text-secondary)", transition: "all 0.15s",
                            textTransform: "capitalize"
                          }}
                        >{ch.replace("_", " ")}</button>
                      ))}
                    </div>

                    {/* Subject line */}
                    <div style={{ marginBottom: 14 }}>
                      <label style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                        SUBJECT LINE
                      </label>
                      <input
                        className="cs-input"
                        value={commResult?.subject || `Checking in on your ChurnShield ${currentMeta.label} account`}
                        onChange={(e) => setCommResult((p) => ({ ...p, subject: e.target.value }))}
                        style={{ fontSize: 13 }}
                      />
                    </div>

                    {/* Body */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)" }}>
                          MESSAGE COPY
                        </label>
                        {commResult && (
                          <span style={{ fontSize: 10, background: "#EEF2FF", color: "var(--primary)", padding: "2px 8px", borderRadius: 20, fontWeight: 600 }}>AI Generated</span>
                        )}
                      </div>
                      <textarea
                        rows={10}
                        className="cs-input"
                        style={{ resize: "none", lineHeight: 1.7, fontSize: 13 }}
                        value={commResult?.body || commResult?.content || `Hi [Contact Name],\n\nI noticed your account activity has dipped recently, and I wanted to personally reach out to ensure you are getting the most out of your ${currentMeta.label} plan.\n\nTo help align our service with your needs, we would like to offer you a custom account review and 15% discount for the next 3 months.\n\nWould you be open to a brief 5-minute chat this week to discuss this offer?\n\nBest regards,\nCustomer Success Team`}
                        onChange={(e) => setCommResult((p) => ({ ...p, body: e.target.value, content: e.target.value }))}
                      />
                    </div>

                    {/* Footer buttons: Replace Send Email with Copy */}
                    <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                      <button className="cs-btn-secondary" style={{ flex: 1, justifyContent: "center" }} onClick={generateComm} disabled={loading}>
                        <RefreshCw size={14} className={loading ? "spin-slow" : ""} /> AI Draft
                      </button>
                      <button
                        className="cs-btn-primary"
                        style={{
                          flex: 2, justifyContent: "center", borderRadius: 10,
                          background: copied ? "#10B981" : "var(--primary)",
                          transition: "all 0.2s ease"
                        }}
                        onClick={() => {
                          const textToCopy = commResult?.body || commResult?.content || `Hi [Contact Name],\n\nI noticed your account activity has dipped recently, and I wanted to personally reach out to ensure you are getting the most out of your ${currentMeta.label} plan.\n\nTo help align our service with your needs, we would like to offer you a custom account review and 15% discount for the next 3 months.\n\nWould you be open to a brief 5-minute chat this week to discuss this offer?\n\nBest regards,\nCustomer Success Team`;
                          navigator.clipboard.writeText(textToCopy);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                      >
                        {copied ? <Check size={15} /> : <Copy size={15} />}
                        <span>{copied ? "Copied to Clipboard!" : "Copy Communication"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

      </main>

      {/* ── Dataset Requirements Modal ── */}
      {showReqModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(17,24,39,0.5)", zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", padding: 24, backdropFilter: "blur(4px)" }}>
          <div className="cs-card" style={{ maxWidth: 440, width: "100%", padding: 28 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#111827" }}>Dataset Requirements — {currentMeta.label}</h3>
              <button onClick={() => setShowReqModal(false)} className="cs-btn-ghost" style={{ padding: 4 }}><X size={16} /></button>
            </div>
            <p style={{ fontSize: 12.5, color: "var(--text-secondary)", marginBottom: 16 }}>Ensure your CSV includes these key columns for the {currentMeta.label} model.</p>
            <div style={{ background: "#F9FAFB", borderRadius: 10, border: "1px solid var(--border)", padding: 16, maxHeight: 280, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
              {DOMAIN_FIELDS[industry].map((f) => (
                <div key={f.key} style={{ fontSize: 12, color: "#374151" }}>
                  <span style={{ color: "var(--primary)", fontWeight: 600 }}>{f.key}</span> — {f.label}
                </div>
              ))}
            </div>
            <button className="cs-btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 16, borderRadius: 10 }} onClick={() => setShowReqModal(false)}>Got it</button>
          </div>
        </div>
      )}
    </div>
  );
}
