import { AppleStyleCarousel } from './components/AppleStyleCarousel'
import { ChatPanel } from './components/ChatPanel'
import { GlassSurface } from './components/GlassSurface'
import { MeshBackdrop } from './components/MeshBackdrop'

function App() {
  return (
    <div className="relative flex min-h-dvh flex-col text-white">
      <MeshBackdrop />

      <header className="sticky top-0 z-20 px-4 pt-6 md:px-8">
        <GlassSurface className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3 md:px-7">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/20 text-sm font-semibold shadow-inner dark:bg-white/10">
              A
            </span>
            <div className="text-left">
              <p className="text-sm font-semibold tracking-tight">Ardeno Glass</p>
              <p className="text-xs text-white/55">Liquid UI kit</p>
            </div>
          </div>
          <nav
            aria-label="Primary"
            className="hidden items-center gap-6 text-sm text-white/75 md:flex"
          >
            <a className="transition hover:text-white" href="#showcase">
              Showcase
            </a>
            <a className="transition hover:text-white" href="#stack">
              Stack
            </a>
            <a className="transition hover:text-white" href="#chat">
              Chat
            </a>
          </nav>
          <a
            href="https://21st.dev"
            target="_blank"
            rel="noreferrer"
            className="rounded-full bg-white/20 px-4 py-2 text-sm font-medium text-white shadow-inner transition hover:bg-white/28 dark:bg-white/12 dark:hover:bg-white/18"
          >
            21st.dev
          </a>
        </GlassSurface>
      </header>

      <main className="relative z-10 flex flex-1 flex-col items-center px-4 py-14 md:px-8 md:py-20">
        <section className="mb-16 max-w-3xl text-center">
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.28em] text-white/45">
            Glassmorphism
          </p>
          <h1 className="text-[clamp(2rem,6vw,3.25rem)] font-semibold leading-[1.1] tracking-tight">
            Interfaces with Apple-style clarity
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-white/60">
            Blur-rich surfaces, luminous borders, and calm typography. Paste
            components from{' '}
            <span className="text-white/85">21st.dev</span>,{' '}
            <span className="text-white/85">shadcn/ui</span>, or DaisyUI onto
            this shell — Tailwind primitives match those ecosystems.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#showcase"
              className="rounded-full bg-white px-6 py-2.5 text-sm font-semibold text-neutral-950 shadow-lg shadow-black/20 transition hover:bg-white/90"
            >
              View showcase
            </a>
            <GlassSurface className="border-white/30 px-6 py-2.5 dark:border-white/12">
              <span className="text-sm font-medium text-white">
                Compatible with HyperUI patterns
              </span>
            </GlassSurface>
          </div>
        </section>

        <section id="showcase" className="mb-20 w-full scroll-mt-28">
          <AppleStyleCarousel />
        </section>

        <section className="mb-20 w-full flex justify-center">
          <ChatPanel />
        </section>

        <section
          id="stack"
          className="grid w-full max-w-5xl scroll-mt-28 gap-4 md:grid-cols-3"
        >
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
            <GlassSurface key={item.title} className="p-6 text-left">
              <h3 className="text-base font-semibold text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/60">
                {item.body}
              </p>
            </GlassSurface>
          ))}
        </section>
      </main>

      <footer className="relative z-10 px-4 pb-10 pt-6 text-center md:px-8">
        <GlassSurface className="mx-auto inline-flex flex-wrap items-center justify-center gap-x-6 gap-y-2 px-8 py-4 text-xs text-white/50">
          <span>Glass demo — swap in your favicon picks from Icons / React Bits.</span>
        </GlassSurface>
      </footer>
    </div>
  )
}

export default App
