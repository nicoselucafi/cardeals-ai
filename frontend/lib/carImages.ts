/**
 * Car image utilities - generates placeholder images based on make/model
 */

// Model-specific gradient colors (tailwind classes)
const MODEL_GRADIENTS: Record<string, { from: string; to: string; accent: string }> = {
  // Toyota SUVs
  "4runner": { from: "from-emerald-900", to: "to-emerald-950", accent: "text-emerald-400" },
  "rav4": { from: "from-blue-900", to: "to-blue-950", accent: "text-blue-400" },
  "highlander": { from: "from-slate-800", to: "to-slate-950", accent: "text-slate-300" },
  "grand highlander": { from: "from-zinc-800", to: "to-zinc-950", accent: "text-zinc-300" },
  "sequoia": { from: "from-amber-900", to: "to-amber-950", accent: "text-amber-400" },
  "venza": { from: "from-purple-900", to: "to-purple-950", accent: "text-purple-400" },
  "land cruiser": { from: "from-stone-800", to: "to-stone-950", accent: "text-stone-300" },
  "bz4x": { from: "from-cyan-900", to: "to-cyan-950", accent: "text-cyan-400" },
  "corolla cross": { from: "from-teal-900", to: "to-teal-950", accent: "text-teal-400" },

  // Toyota Sedans
  "camry": { from: "from-red-900", to: "to-red-950", accent: "text-red-400" },
  "corolla": { from: "from-sky-900", to: "to-sky-950", accent: "text-sky-400" },
  "prius": { from: "from-green-900", to: "to-green-950", accent: "text-green-400" },
  "crown": { from: "from-indigo-900", to: "to-indigo-950", accent: "text-indigo-400" },
  "mirai": { from: "from-violet-900", to: "to-violet-950", accent: "text-violet-400" },

  // Toyota Trucks
  "tacoma": { from: "from-orange-900", to: "to-orange-950", accent: "text-orange-400" },
  "tundra": { from: "from-yellow-900", to: "to-yellow-950", accent: "text-yellow-400" },

  // Toyota Sports
  "gr86": { from: "from-rose-900", to: "to-rose-950", accent: "text-rose-400" },
  "gr corolla": { from: "from-fuchsia-900", to: "to-fuchsia-950", accent: "text-fuchsia-400" },
  "gr supra": { from: "from-pink-900", to: "to-pink-950", accent: "text-pink-400" },

  // Toyota Minivan
  "sienna": { from: "from-blue-800", to: "to-blue-950", accent: "text-blue-300" },

  // Honda
  "accord": { from: "from-slate-800", to: "to-slate-950", accent: "text-slate-300" },
  "civic": { from: "from-blue-900", to: "to-blue-950", accent: "text-blue-400" },
  "cr-v": { from: "from-emerald-900", to: "to-emerald-950", accent: "text-emerald-400" },
  "hr-v": { from: "from-teal-900", to: "to-teal-950", accent: "text-teal-400" },
  "pilot": { from: "from-zinc-800", to: "to-zinc-950", accent: "text-zinc-300" },
  "passport": { from: "from-amber-900", to: "to-amber-950", accent: "text-amber-400" },
  "ridgeline": { from: "from-orange-900", to: "to-orange-950", accent: "text-orange-400" },
  "odyssey": { from: "from-indigo-900", to: "to-indigo-950", accent: "text-indigo-400" },
  "prologue": { from: "from-cyan-900", to: "to-cyan-950", accent: "text-cyan-400" },
  "insight": { from: "from-green-900", to: "to-green-950", accent: "text-green-400" },

  // Tesla
  "model 3": { from: "from-gray-800", to: "to-gray-950", accent: "text-red-500" },
  "model y": { from: "from-gray-800", to: "to-gray-950", accent: "text-red-500" },
  "model s": { from: "from-zinc-800", to: "to-zinc-950", accent: "text-red-500" },
  "model x": { from: "from-zinc-800", to: "to-zinc-950", accent: "text-red-500" },
  "cybertruck": { from: "from-neutral-700", to: "to-neutral-950", accent: "text-red-500" },
};

// Make-specific fallback gradients
const MAKE_GRADIENTS: Record<string, { from: string; to: string; accent: string }> = {
  toyota: { from: "from-red-900", to: "to-red-950", accent: "text-red-400" },
  honda: { from: "from-blue-900", to: "to-blue-950", accent: "text-blue-400" },
  tesla: { from: "from-gray-800", to: "to-gray-950", accent: "text-red-500" },
  default: { from: "from-gray-800", to: "to-gray-950", accent: "text-gray-400" },
};

export interface CarImageConfig {
  gradient: {
    from: string;
    to: string;
    accent: string;
  };
}

/**
 * Get image configuration for a car based on make/model
 */
export function getCarImageConfig(make: string, model: string): CarImageConfig {
  const normalizedModel = model.toLowerCase();
  const normalizedMake = make.toLowerCase();

  // Try model-specific first
  const modelGradient = MODEL_GRADIENTS[normalizedModel];
  if (modelGradient) {
    return { gradient: modelGradient };
  }

  // Fall back to make-specific
  const makeGradient = MAKE_GRADIENTS[normalizedMake] || MAKE_GRADIENTS.default;
  return { gradient: makeGradient };
}

/**
 * Get a display-friendly vehicle type icon name
 */
export function getVehicleType(model: string): "suv" | "sedan" | "truck" | "sports" | "minivan" | "electric" {
  const normalizedModel = model.toLowerCase();

  // SUVs
  if (["4runner", "rav4", "highlander", "grand highlander", "sequoia", "venza", "land cruiser", "corolla cross", "cr-v", "hr-v", "pilot", "passport"].includes(normalizedModel)) {
    return "suv";
  }

  // Trucks
  if (["tacoma", "tundra", "ridgeline"].includes(normalizedModel)) {
    return "truck";
  }

  // Sports cars
  if (["gr86", "gr corolla", "gr supra"].includes(normalizedModel)) {
    return "sports";
  }

  // Minivans
  if (["sienna", "odyssey"].includes(normalizedModel)) {
    return "minivan";
  }

  // Electric (including Tesla)
  if (["bz4x", "mirai", "prius", "prologue", "model 3", "model y", "model s", "model x", "insight"].includes(normalizedModel)) {
    return "electric";
  }

  // Trucks (Cybertruck)
  if (["cybertruck"].includes(normalizedModel)) {
    return "truck";
  }

  // Default to sedan
  return "sedan";
}
