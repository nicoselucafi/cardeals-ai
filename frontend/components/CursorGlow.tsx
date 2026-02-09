"use client";

import { useEffect, useState, useMemo } from "react";

export default function CursorGlow() {
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const [isVisible, setIsVisible] = useState(false);

  const TILE_SIZE = 60;
  const EFFECT_RADIUS = 180;

  // Only generate tiles within the effect radius of the cursor
  const activeTiles = useMemo(() => {
    if (!isVisible || mousePos.x < 0) return [];

    const tiles: Array<{ id: string; x: number; y: number; distance: number }> = [];

    // Calculate the grid cells that could be affected
    const startCol = Math.max(0, Math.floor((mousePos.x - EFFECT_RADIUS) / TILE_SIZE));
    const endCol = Math.ceil((mousePos.x + EFFECT_RADIUS) / TILE_SIZE);
    const startRow = Math.max(0, Math.floor((mousePos.y - EFFECT_RADIUS) / TILE_SIZE));
    const endRow = Math.ceil((mousePos.y + EFFECT_RADIUS) / TILE_SIZE);

    for (let row = startRow; row <= endRow; row++) {
      for (let col = startCol; col <= endCol; col++) {
        const x = col * TILE_SIZE;
        const y = row * TILE_SIZE;
        const tileCenterX = x + TILE_SIZE / 2;
        const tileCenterY = y + TILE_SIZE / 2;
        const distance = Math.sqrt(
          Math.pow(mousePos.x - tileCenterX, 2) +
          Math.pow(mousePos.y - tileCenterY, 2)
        );

        if (distance <= EFFECT_RADIUS) {
          tiles.push({
            id: `${col}-${row}`,
            x,
            y,
            distance,
          });
        }
      }
    }

    return tiles;
  }, [mousePos.x, mousePos.y, isVisible]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
      if (!isVisible) setIsVisible(true);
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    const handleMouseEnter = () => {
      setIsVisible(true);
    };

    window.addEventListener("mousemove", handleMouseMove);
    document.body.addEventListener("mouseleave", handleMouseLeave);
    document.body.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
    };
  }, [isVisible]);

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {/* Base grid pattern - always visible but subtle */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: `${TILE_SIZE}px ${TILE_SIZE}px`,
        }}
      />

      {/* Interactive tiles - only render those near cursor */}
      {activeTiles.map((tile) => {
        const intensity = 1 - tile.distance / EFFECT_RADIUS;
        const scale = 1 + intensity * 0.12;
        const borderOpacity = 0.1 + intensity * 0.5;
        const bgOpacity = intensity * 0.12;

        return (
          <div
            key={tile.id}
            className="absolute rounded-sm"
            style={{
              left: tile.x + 1,
              top: tile.y + 1,
              width: TILE_SIZE - 2,
              height: TILE_SIZE - 2,
              transform: `scale(${scale})`,
              border: `1px solid rgba(0, 212, 255, ${borderOpacity})`,
              background: `rgba(0, 212, 255, ${bgOpacity})`,
              transformOrigin: "center center",
              transition: "transform 0.15s ease-out, border-color 0.15s ease-out, background 0.15s ease-out",
            }}
          />
        );
      })}

      {/* Subtle ambient glow at cursor position */}
      <div
        className="absolute rounded-full"
        style={{
          left: mousePos.x - 150,
          top: mousePos.y - 150,
          width: 300,
          height: 300,
          opacity: isVisible ? 1 : 0,
          background: "radial-gradient(circle, rgba(0, 212, 255, 0.08) 0%, transparent 70%)",
          transition: "opacity 0.3s ease-out",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
