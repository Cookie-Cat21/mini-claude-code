export function MeshBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#050508]"
    >
      <div className="absolute -left-[18%] top-[-24%] h-[76vmin] w-[76vmin] rounded-full bg-[#6366f1]/45 blur-[120px]" />
      <div className="absolute -right-[20%] top-[14%] h-[70vmin] w-[70vmin] rounded-full bg-[#c084fc]/34 blur-[115px]" />
      <div className="absolute bottom-[-24%] left-[22%] h-[64vmin] w-[64vmin] rounded-full bg-[#22d3ee]/28 blur-[110px]" />
      <div className="absolute left-1/2 top-1/2 h-[90vmin] w-[90vmin] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7c3aed]/18 blur-[145px]" />
      <div className="absolute left-[22%] top-[18%] h-32 w-32 rounded-full bg-white/10 blur-[70px]" />
      <div
        className="absolute inset-0 opacity-[0.3]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)
          `,
          backgroundSize: '52px 52px',
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_76%_48%_at_50%_14%,rgba(255,255,255,0.09),transparent_56%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(115deg,rgba(255,255,255,0.05),transparent_24%,transparent_70%,rgba(255,255,255,0.035))]" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#050508]/10 via-[#050508]/28 to-[#050508]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#050508_82%)] opacity-78" />
    </div>
  )
}
