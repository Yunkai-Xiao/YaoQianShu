const request = require('supertest');
jest.mock('yahoo-finance2', () => ({
  default: {
    quote: jest.fn(async () => ({ regularMarketPrice: 123.45 }))
  }
}));
const app = require('../server');

describe('API', () => {
  it('returns stock price', async () => {
    const res = await request(app).get('/api/stock/SPY');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('price', 123.45);
  });
});
