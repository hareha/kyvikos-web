import './site.css';

const SECTIONS = ['about', 'services', 'portfolio', 'contact'];

/** 소개서 35p 고객사 로고 */
const CLIENTS = [
  'HS효성', '성동구', '현대자동차', '숨프로젝트', 'APEC CEO Summit Korea 2025',
  '홍콩의류제조협회', '파라다이스', '국가보훈부', 'firay water', 'YG엔터테인먼트',
  'UNIX', '노블레스', '효성', '일지재단', '동국산업',
  '광복회', 'TV조선', '세방여행', 'LTC',
];

/** 3D 메인 아래 페이지의 스크롤 동작 */
export function initSite({ loadVenue, setRendering }) {
  renderClients();
  document.body.classList.add('anim');

  document.addEventListener('click', (e) => {
    const anchor = e.target.closest('a[data-scroll]');
    if (anchor) {
      e.preventDefault();
      document.getElementById(anchor.getAttribute('href').slice(1))?.scrollIntoView({ behavior: 'smooth' });
      return;
    }
    if (e.target.closest('[data-scroll-top]')) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    const card = e.target.closest('[data-venue-card]');
    if (card) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      loadVenue(card.dataset.venueCard);
    }
  });

  // 3D가 화면에서 벗어나면 렌더링을 멈춰 배터리·발열을 아낀다
  const hero = document.getElementById('hero');
  new IntersectionObserver(
    ([entry]) => {
      document.body.classList.toggle('scrolled', entry.intersectionRatio < 0.45);
      setRendering(entry.intersectionRatio > 0.01);
    },
    { threshold: [0, 0.01, 0.45, 1] },
  ).observe(hero);

  const riseObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('in');
        riseObserver.unobserve(entry.target);
      }
    },
    { threshold: 0.12 },
  );
  document.querySelectorAll('.rise').forEach((el) => riseObserver.observe(el));

  // 현재 보고 있는 섹션을 네비게이션에 표시
  const links = new Map(
    [...document.querySelectorAll('.topbar nav a[data-scroll]')].map((a) => [a.getAttribute('href').slice(1), a]),
  );
  const spy = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        links.forEach((a, id) => a.classList.toggle('current', id === entry.target.id));
      }
    },
    { rootMargin: '-45% 0px -50% 0px' },
  );
  for (const id of SECTIONS) {
    const el = document.getElementById(id);
    if (el) spy.observe(el);
  }
}

/** 주소의 #해시가 공간 id가 아니라 페이지 섹션인지 */
export const isSectionHash = (hash) => SECTIONS.includes(hash);

function renderClients() {
  const host = document.getElementById('clients');
  if (!host) return;
  const base = import.meta.env.BASE_URL;
  host.innerHTML = CLIENTS.map(
    (name, i) => `<div><img src="${base}images/site/clients/c${i + 1}.png" alt="${name}" loading="lazy" /></div>`,
  ).join('');
}
