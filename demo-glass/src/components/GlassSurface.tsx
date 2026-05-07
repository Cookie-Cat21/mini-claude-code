import type { ComponentProps } from 'react'

const base =
  'rounded-[26px] border border-white/25 bg-white/15 shadow-[0_12px_40px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.45)] backdrop-blur-3xl backdrop-saturate-[1.8] dark:border-white/10 dark:bg-white/[0.07] dark:shadow-[0_24px_80px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.12)]'

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
