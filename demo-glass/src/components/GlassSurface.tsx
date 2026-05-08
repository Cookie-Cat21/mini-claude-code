import type { ComponentProps } from 'react'

const base =
  'rounded-[26px] border border-white/[0.22] bg-white/[0.14] shadow-[0_8px_32px_rgba(0,0,0,0.2),0_1px_0_rgba(255,255,255,0.55)_inset,0_0_0_1px_rgba(255,255,255,0.06)_inset] backdrop-blur-3xl backdrop-saturate-[1.85] dark:border-white/[0.11] dark:bg-white/[0.065] dark:shadow-[0_28px_90px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.14),inset_0_0_0_1px_rgba(255,255,255,0.04)]'

export function GlassSurface({
  className = '',
  children,
  ...rest
}: ComponentProps<'div'>) {
  return (
    <div className={`${base} ${className}`.trim()} {...rest}>
      {children}
    </div>
  )
}
