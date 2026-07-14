const accounts = {
  ui: {
    username: process.env.TEST_USERNAME || 'ZhaoShengYao',
    password: process.env.TEST_PASSWORD || '123456'
  },
  api: {
    username: process.env.API_USERNAME || process.env.TEST_USERNAME || 'ZhaoShengYao',
    password: process.env.API_PASSWORD || process.env.TEST_PASSWORD || '123456'
  }
};

export default accounts;