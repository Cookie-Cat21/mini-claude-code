import { GlassSurface } from './GlassSurface'

type Card = {
  title: string
  subtitle: string
  hue: string
}

const CARDS: Card[] = [
  {
    title: 'Depth',
    subtitle: 'Layered translucency and soft specular edges',
    hue: 'from-indigo-500/30 to-purple-600/20',
  },
  {
    title: 'Motion',
    subtitle: 'Scroll-snap rhythm with calm, continuous flow',
    hue: 'from-fuchsia-500/25 to-pink-500/15',
  },
  {
    title: 'Material',
    subtitle: 'Blur, saturation, and hairline luminance',
    hue: 'from-cyan-500/25 to-blue-600/20',
  },
  {
    title: 'Compose',
    subtitle: 'Drop in blocks from shadcn / 21st / HyperUI',
    hue: 'from-emerald-500/20 to-teal-600/15',
  },
]

export function AppleStyleCarousel() {
  return (
    <section className="w-full max-w-6xl px-4">
      <p className="mb-3 text-center text-xs font-medium uppercase tracking-[0.2em] text-white/50">
        Featured
      </p>
      <h2 className="mb-8 text-center text-2xl font-semibold tracking-tight text-white md:text-3xl">
        Cards with glass depth
      </h2>
      <div className="relative">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-[#070709] via-[#070709]/85 to-transparent sm:w-14 md:w-[4.5rem]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-[#070709] via-[#070709]/85 to-transparent sm:w-14 md:w-[4.5rem]"
        />
        <div
          className="-mx-4 flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-4 pt-1 [scrollbar-width:none] md:gap-6 [&::-webkit-scrollbar]:hidden"
          role="region"
          aria-label="Feature cards carousel"
        >
          {CARDS.map((c) => (
            <article
              key={c.title}
              className="min-w-[min(100%,320px)] shrink-0 snap-center md:min-w-[340px]"
            >
              <GlassSurface className="flex h-full min-h-[280px] flex-col overflow-hidden p-0 transition duration-500 ease-out hover:-translate-y-1 hover:shadow-[0_28px_70px_rgba(0,0,0,0.45)]">
                <div
                  className={`relative h-28 overflow-hidden bg-gradient-to-br ${c.hue} opacity-[0.92]`}
                >
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/45 to-transparent" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/25 to-transparent" />
                </div>
                <div className="flex flex-1 flex-col justify-end p-6 text-left">
                  <h3 className="text-lg font-semibold tracking-tight text-white">
                    {c.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-white/65">
                    {c.subtitle}
                  </p>
                </div>
              </GlassSurface>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
