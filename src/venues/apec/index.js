export { project, views } from './data.js';
export { build } from './scene.js';

export const env = {
  height: 74,
  sky: { zenith: '#02040b', horizon: '#1b2644', moon: [-0.45, 0.32, -0.83] },
  stars: true,
  fog: 0.0026,
  exposure: 1,
  hdri: 'moonless_golf',
  envIntensity: 1.5,
};
