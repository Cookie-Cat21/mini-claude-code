import { MeshBackdrop } from './components/MeshBackdrop'
import { MiniCodeChat } from './components/MiniCodeChat'

function App() {
  return (
    <div className="relative flex min-h-dvh flex-col text-white">
      <MeshBackdrop />

      <main className="relative z-10 flex min-h-0 flex-1 flex-col items-center justify-center px-4 py-8 md:px-8">
        <MiniCodeChat />
      </main>
    </div>
  )
}

export default App
