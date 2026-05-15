import type { Locale } from "./i18n";

const OPTIONS = {
  id: {
    industries: [
      "Pelatihan korporat",
      "EdTech / L&D",
      "Manufaktur B2B",
      "Distribusi / grosir",
      "Jasa profesional",
      "Retail / F&B",
      "Lainnya",
    ],
    companySizes: [
      "1–10 karyawan",
      "11–50 karyawan",
      "51–200 karyawan",
      "201–500 karyawan",
      "500+ karyawan",
    ],
    buyerRoles: [
      "Founder / Pemilik",
      "Direktur Operasional",
      "Head of Sales",
      "Head of HR / L&D",
      "Manajer Pemasaran",
      "Lainnya",
    ],
    salesVoices: [
      "Formal tapi hangat (Bahasa Indonesia bisnis)",
      "Santai dan personal (seperti chat WA profesional)",
      "Teknis dan data-driven",
      "Konsultatif — banyak bertanya",
      "Kustom (jelaskan di bawah)",
    ],
    other: "Lainnya",
  },
  en: {
    industries: [
      "Corporate training",
      "EdTech / L&D",
      "B2B manufacturing",
      "Distribution / wholesale",
      "Professional services",
      "Retail / F&B",
      "Other",
    ],
    companySizes: [
      "1–10 employees",
      "11–50 employees",
      "51–200 employees",
      "201–500 employees",
      "500+ employees",
    ],
    buyerRoles: [
      "Founder / Owner",
      "Director of Operations",
      "Head of Sales",
      "Head of HR / L&D",
      "Marketing Manager",
      "Other",
    ],
    salesVoices: [
      "Formal but warm (business Indonesian)",
      "Casual and personal (professional chat style)",
      "Technical and data-driven",
      "Consultative — asks questions",
      "Custom (describe below)",
    ],
    other: "Other",
  },
} as const;

export const CURRENCIES = ["IDR", "USD", "SGD", "MYR"];

export function getCampaignOptions(locale: Locale) {
  const o = OPTIONS[locale];
  return {
    industries: [...o.industries],
    companySizes: [...o.companySizes],
    buyerRoles: [...o.buyerRoles],
    salesVoices: [...o.salesVoices],
    otherLabel: o.other,
  };
}

export function suggestMaxLeads(
  revenueTarget: number,
  minPrice: number,
  maxPrice: number,
): number {
  if (!revenueTarget || revenueTarget <= 0) return 10;
  const avg = Math.max((minPrice + maxPrice) / 2, 1);
  const dealsNeeded = revenueTarget / avg;
  const processed = dealsNeeded / (0.3 * 0.1);
  return Math.max(3, Math.min(50, Math.ceil(processed)));
}
