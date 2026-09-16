import './site.css';

const SECTIONS = ['about', 'experience', 'services', 'portfolio', 'contact'];

/** 소개서 35p 고객사 로고 */
const CLIENTS = [
  'HS효성', '성동구', '현대자동차', '숨프로젝트', 'APEC CEO Summit Korea 2025',
  '홍콩의류제조협회', '파라다이스', '국가보훈부', 'firay water', 'YG엔터테인먼트',
  'UNIX', '노블레스', '효성', '일지재단', '동국산업',
  '광복회', 'TV조선', '세방여행', 'LTC',
];

const scrollToSection = (id, behavior = 'smooth') => {
  // 3D 투어는 화면 전체로 보이도록 고정 영역 위치로 맞춘다
  const el = id === 'experience' ? document.querySelector('#experience .stage') : document.getElementById(id);
  el?.scrollIntoView({ behavior, block: 'start' });
};

/** 페이지 스크롤 동작 (3D는 '3D 투어' 섹션 안에 들어 있다) */
export function initSite({ loadVenue, setRendering }) {
  renderClients();
  document.body.classList.add('anim');

  document.addEventListener('click', (e) => {
    const anchor = e.target.closest('[data-scroll]');
    if (anchor) {
      e.preventDefault();
      scrollToSection(anchor.getAttribute('href').slice(1));
      return;
    }
    if (e.target.closest('[data-scroll-top]')) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    const card = e.target.closest('[data-venue-card]');
    if (card) {
      loadVenue(card.dataset.venueCard);
      scrollToSection('experience');
    }
  });

  // 3D가 화면 밖이면 렌더링을 멈춰 배터리·발열을 아낀다
  new IntersectionObserver(([entry]) => setRendering(entry.isIntersecting), { threshold: 0 }).observe(
    document.getElementById('experience'),
  );

  // 첫 화면을 벗어나면 헤더에 배경을 깐다
  const onScroll = () => document.body.classList.toggle('scrolled', window.scrollY > 80);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

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

  // 공간 링크(#apec 등)로 들어오면 3D 투어부터 보여준다
  const hash = location.hash.slice(1);
  if (hash && !isSectionHash(hash)) {
    requestAnimationFrame(() => scrollToSection('experience', 'instant'));
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
