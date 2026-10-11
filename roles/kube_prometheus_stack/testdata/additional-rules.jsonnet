{
  'site-custom': {
    groups: [
      {
        name: 'site.custom',
        rules: [
          {
            alert: 'SiteCustomAlert',
            expr: 'vector(1) == 1',
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              summary: 'A site-specific condition is active',
            },
          },
        ],
      },
    ],
  },
}
