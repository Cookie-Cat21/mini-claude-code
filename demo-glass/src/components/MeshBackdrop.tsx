export function MeshBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#0a0a0c]"
    >
      <div className="absolute -left-1/4 top-[-20%] h-[70vmin] w-[70vmin] rounded-full bg-[#4f46e5]/40 blur-[100px]" />
      <div className="absolute -right-1/4 top-1/3 h-[60vmin] w-[60vmin] rounded-full bg-[#a855f7]/35 blur-[100px]" />
      <div className="absolute bottom-[-15%] left-1/3 h-[55vmin] w-[55vmin] rounded-full bg-[#06b6d4]/30 blur-[100px]" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0a0c]/30 to-[#0a0a0c]" />
    </div>
  )
}
