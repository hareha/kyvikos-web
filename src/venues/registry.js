// 공간 목록. 각 공간 모듈은 { project, views, env, build } 를 export 합니다.
// 규약은 src/venues/README.md 참고.
export const venues = [
  { id: 'apec', label: 'APEC 황룡원', load: () => import('./apec/index.js') },
  { id: 'hyundai', label: '현대 모터스튜디오', load: () => import('./hyundai/index.js') },
  { id: 'basquiat', label: 'DDP 바스키아', load: () => import('./basquiat/index.js') },
  { id: 'localpower', label: '성수 LOCAL POWER', load: () => import('./localpower/index.js') },
];
