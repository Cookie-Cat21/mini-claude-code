export function MeshBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#070709]"
    >
      <div className="absolute -left-1/4 top-[-20%] h-[72vmin] w-[72vmin] rounded-full bg-[#6366f1]/42 blur-[110px]" />
      <div className="absolute -right-1/4 top-[28%] h-[62vmin] w-[62vmin] rounded-full bg-[#c084fc]/38 blur-[105px]" />
      <div className="absolute bottom-[-18%] left-[28%] h-[58vmin] w-[58vmin] rounded-full bg-[#22d3ee]/32 blur-[100px]" />
      <div className="absolute left-1/2 top-1/2 h-[85vmin] w-[85vmin] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7c3aed]/15 blur-[130px]" />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_55%_at_50%_20%,rgba(255,255,255,0.06),transparent_55%)]" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#070709]/25 to-[#070709]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#070709_78%)] opacity-80" />
    </div>
  )
}
