const STORAGE_KEY = "cardealsai_saved_offers";

export function getSavedOffers(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

export function saveOffer(offerId: string): void {
  const saved = getSavedOffers();
  if (!saved.includes(offerId)) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...saved, offerId]));
  }
}

export function removeSavedOffer(offerId: string): void {
  const saved = getSavedOffers().filter((id) => id !== offerId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
}

export function toggleSavedOffer(offerId: string): boolean {
  const saved = getSavedOffers();
  if (saved.includes(offerId)) {
    removeSavedOffer(offerId);
    return false;
  } else {
    saveOffer(offerId);
    return true;
  }
}

export function isOfferSaved(offerId: string): boolean {
  return getSavedOffers().includes(offerId);
}

export function clearAllSaved(): void {
  localStorage.removeItem(STORAGE_KEY);
}
