import { AppleStyleCarousel } from './components/AppleStyleCarousel'
import { GlassSurface } from './components/GlassSurface'
import { MeshBackdrop } from './components/MeshBackdrop'

function App() {
  return (
    <div className="relative flex min-h-dvh flex-col text-white">
      <MeshBackdrop />

      <header className="sticky top-0 z-20 px-4 pt-6 md:px-8">
        <GlassSurface className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3.5 md:px-7">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-white/35 to-white/10 text-sm font-semibold text-white shadow-lg shadow-black/15 ring-1 ring-white/25 dark:from-white/25 dark:to-white/5 dark:ring-white/15">
              A
            </span>
            <div className="text-left">
              <p className="text-sm font-semibold tracking-tight">Ardeno Glass</p>
              <p className="text-xs text-white/55">Liquid UI kit</p>
            </div>
          </div>
          <nav
            aria-label="Primary"
            className="hidden items-center gap-1 text-sm text-white/72 md:flex"
          >
            <a
              className="rounded-full px-3 py-1.5 transition hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/40"
              href="#showcase"
            >
              Showcase
            </a>
            <a
              className="rounded-full px-3 py-1.5 transition hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/40"
              href="#stack"
            >
              Stack
            </a>
          </nav>
          <a
            href="https://21st.dev"
            target="_blank"
            rel="noreferrer"
            className="rounded-full bg-white/20 px-4 py-2 text-sm font-medium text-white shadow-inner ring-1 ring-white/15 transition hover:bg-white/30 hover:ring-white/25 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/45 dark:bg-white/12 dark:hover:bg-white/18"
          >
            21st.dev
          </a>
        </GlassSurface>
      </header>

      <main className="relative z-10 flex flex-1 flex-col items-center px-4 py-14 md:px-8 md:py-20">
        <section className="relative mb-16 max-w-3xl text-center">
          <div
            aria-hidden
            className="pointer-events-none absolute left-1/2 top-1/2 h-[min(28rem,70vw)] w-[min(28rem,70vw)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#a78bfa]/12 blur-[90px]"
          />
          <p className="relative mb-4 text-xs font-medium uppercase tracking-[0.28em] text-white/45">
            Glassmorphism
          </p>
          <h1 className="relative text-[clamp(2rem,6vw,3.25rem)] font-semibold leading-[1.08] tracking-tight text-white">
            Interfaces with{' '}
            <span className="bg-gradient-to-r from-white via-[#e8e4ff] to-[#c4b5fd] bg-clip-text text-transparent">
              Apple-style clarity
            </span>
          </h1>
          <p className="relative mx-auto mt-5 max-w-xl text-base leading-relaxed text-white/62">
            Blur-rich surfaces, luminous borders, and calm typography. Paste
            components from{' '}
            <span className="font-medium text-white/88">21st.dev</span>,{' '}
            <span className="font-medium text-white/88">shadcn/ui</span>, or DaisyUI onto
            this shell — Tailwind primitives match those ecosystems.
          </p>

          <div className="relative mt-10 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#showcase"
              className="rounded-full bg-white px-6 py-2.5 text-sm font-semibold text-neutral-950 shadow-lg shadow-black/25 ring-1 ring-white/30 transition hover:-translate-y-0.5 hover:bg-white/95 hover:shadow-xl hover:shadow-black/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/55"
            >
              View showcase
            </a>
            <GlassSurface className="border-white/28 px-6 py-2.5 transition hover:border-white/40 dark:border-white/12 dark:hover:border-white/22">
              <span className="text-sm font-medium text-white/95">
                Compatible with HyperUI patterns
              </span>
            </GlassSurface>
          </div>
        </section>

        <section id="showcase" className="mb-20 w-full scroll-mt-28">
          <AppleStyleCarousel />
        </section>

        <section id="stack" className="w-full max-w-5xl scroll-mt-28">
          <p className="mb-2 text-center text-xs font-medium uppercase tracking-[0.2em] text-white/48">
            Why this stack
          </p>
          <h2 className="mb-8 text-center text-lg font-semibold tracking-tight text-white/90 md:text-xl">
            Built for modern component libraries
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                title: '21st & shadcn',
                body: 'Copy React blocks — same utility classes translate here.',
              },
              {
                title: 'Tailwind-first',
                body: 'Use @tailwindcss/vite and compose glass as utilities.',
              },
              {
                title: 'Backdrop filter',
                body: 'Saturate + blur mimic recent Apple system materials.',
              },
            ].map((item) => (
              <GlassSurface
                key={item.title}
                className="group p-6 text-left transition duration-300 hover:-translate-y-1 hover:border-white/35 hover:shadow-[0_20px_50px_rgba(0,0,0,0.35)] dark:hover:border-white/18"
              >
                <span className="mb-3 inline-block h-1 w-8 rounded-full bg-gradient-to-r from-violet-400/90 to-cyan-400/70 opacity-80 transition group-hover:w-10 group-hover:opacity-100" />
                <h3 className="text-base font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-white/62">
                  {item.body}
                </p>
              </GlassSurface>
            ))}
          </div>
        </section>
      </main>

      <footer className="relative z-10 px-4 pb-10 pt-8 text-center md:px-8">
        <GlassSurface className="mx-auto inline-flex max-w-xl flex-col items-center justify-center gap-1 px-8 py-4 text-xs leading-relaxed text-white/50">
          <span className="text-white/58">Glass demo</span>
          <span>Swap in favicon picks from Icons / React Bits.</span>
        </GlassSurface>
      </footer>
    </div>
  )
}

export default App
