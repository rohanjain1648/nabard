import { useEffect, type RefObject } from 'react'

/**
 * Wires the landing page's motion:
 *  - scroll-reveal (.reveal / .stagger gain `.in` when they enter the viewport)
 *  - scroll progress (--sp on <html>) + hero scroll offset (--sy)
 *  - cursor spotlight + parallax tilt on the hero (--mx/--my/--tx/--ty)
 */
export function useLandingMotion(
  rootRef: RefObject<HTMLElement | null>,
  heroRef: RefObject<HTMLElement | null>,
) {
  useEffect(() => {
    const root = rootRef.current
    if (!root) return

    // Scroll reveal
    const targets = root.querySelectorAll<HTMLElement>('.reveal, .stagger')
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('in')
            io.unobserve(e.target)
          }
        })
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' },
    )
    targets.forEach((el) => io.observe(el))

    // Scroll progress + hero offset
    const onScroll = () => {
      const doc = document.documentElement
      const max = doc.scrollHeight - doc.clientHeight || 1
      doc.style.setProperty('--sp', String(Math.min(1, doc.scrollTop / max)))
      heroRef.current?.style.setProperty('--sy', String(window.scrollY))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })

    // Cursor spotlight + parallax
    const hero = heroRef.current
    const onMove = (ev: MouseEvent) => {
      if (!hero) return
      const r = hero.getBoundingClientRect()
      const mx = (ev.clientX - r.left) / r.width
      const my = (ev.clientY - r.top) / r.height
      hero.style.setProperty('--mx', `${mx * 100}%`)
      hero.style.setProperty('--my', `${my * 100}%`)
      hero.style.setProperty('--tx', String(mx - 0.5))
      hero.style.setProperty('--ty', String(my - 0.5))
    }
    const onLeave = () => {
      hero?.style.setProperty('--tx', '0')
      hero?.style.setProperty('--ty', '0')
    }
    hero?.addEventListener('mousemove', onMove)
    hero?.addEventListener('mouseleave', onLeave)

    return () => {
      io.disconnect()
      window.removeEventListener('scroll', onScroll)
      hero?.removeEventListener('mousemove', onMove)
      hero?.removeEventListener('mouseleave', onLeave)
    }
  }, [rootRef, heroRef])
}
