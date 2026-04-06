/** Minimal super-admin navigation (CodeCanyon client — tickets + license registry only). */
export const SUPER_ADMIN_NAV_GROUPS = [
  {
    id: 'overview',
    label: 'Overview',
    items: [
      { label: 'Dashboard', to: '/super-admin', icon: 'ChartBarIcon', match: 'exact' },
    ],
  },
  {
    id: 'revenue',
    label: 'Licensing',
    items: [
      { label: 'Self-hosted licenses', to: '/super-admin/self-hosted-licenses', icon: 'KeyIcon' },
    ],
  },
  {
    id: 'support',
    label: 'Support',
    items: [
      {
        label: 'Ticket queue',
        to: '/super-admin/tickets',
        icon: 'ChatBubbleLeftRightIcon',
        match: 'tickets-queue',
      },
    ],
  },
]
