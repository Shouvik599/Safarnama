import type { RouteStop, DestinationSuggestion } from '../types/trip';

export interface LocationAirport {
  code: string;
  name: string;
  city: string;
  label: string;
}

export interface CircuitDefinition {
  id: string;
  name: string;
  alias: string;
  scope: 'DOMESTIC' | 'INTERNATIONAL';
  visaStatus: string;
  defaultDurationDays: number;
  seasonInsights: Record<string, string>;
  defaultStops: RouteStop[];
  suggestions: DestinationSuggestion[];
}

export const INDIAN_ORIGIN_AIRPORTS: LocationAirport[] = [
  { code: 'DEL', name: 'Indira Gandhi International Airport', city: 'New Delhi', label: 'New Delhi (DEL - Indira Gandhi Intl)' },
  { code: 'BOM', name: 'Chhatrapati Shivaji Maharaj International Airport', city: 'Mumbai', label: 'Mumbai (BOM - Chhatrapati Shivaji)' },
  { code: 'BLR', name: 'Kempegowda International Airport', city: 'Bengaluru', label: 'Bengaluru (BLR - Kempegowda Intl)' },
  { code: 'CCU', name: 'Netaji Subhash Chandra Bose International Airport', city: 'Kolkata', label: 'Kolkata (CCU - Netaji Subhash)' },
  { code: 'MAA', name: 'Chennai International Airport', city: 'Chennai', label: 'Chennai (MAA - Chennai Intl)' },
  { code: 'HYD', name: 'Rajiv Gandhi International Airport', city: 'Hyderabad', label: 'Hyderabad (HYD - Rajiv Gandhi Intl)' },
  { code: 'GOI', name: 'Dabolim Airport', city: 'Goa', label: 'Goa (GOI - Dabolim Airport)' },
  { code: 'COK', name: 'Cochin International Airport', city: 'Kochi', label: 'Kochi (COK - Cochin Intl)' },
  { code: 'AMD', name: 'Sardar Vallabhbhai Patel International Airport', city: 'Ahmedabad', label: 'Ahmedabad (AMD - Sardar Patel Intl)' },
  { code: 'JAI', name: 'Jaipur International Airport', city: 'Jaipur', label: 'Jaipur (JAI - Sanganer Airport)' },
  { code: 'IXL', name: 'Kushok Bakula Rimpochee Airport', city: 'Leh', label: 'Leh Ladakh (IXL - Kushok Bakula)' },
  { code: 'PNQ', name: 'Pune International Airport', city: 'Pune', label: 'Pune (PNQ - Lohegaon)' },
  { code: 'VNS', name: 'Lal Bahadur Shastri Airport', city: 'Varanasi', label: 'Varanasi (VNS - Lal Bahadur Shastri)' },
  { code: 'GAU', name: 'Lokpriya Gopinath Bordoloi International Airport', city: 'Guwahati', label: 'Guwahati (GAU - Lokpriya Gopinath)' },
];

export const PRECONFIGURED_CIRCUITS: CircuitDefinition[] = [
  {
    id: 'japan',
    name: 'Kyoto, Japan (KIX - Kansai Intl / Shinkansen Rail)',
    alias: 'Japan (Autumn Trail)',
    scope: 'INTERNATIONAL',
    visaStatus: 'eVisa Active • 90 Days Single Entry',
    defaultDurationDays: 10,
    seasonInsights: {
      spring: 'Optimal Season: Cherry Blossom (Sakura) & Mild Spring Air',
      summer: 'Summer Festivities: Warm Evening Markets & Mountain Sanctuaries',
      autumn: 'Optimal Season: Pleasant Autumn & Vibrant Maple Foliage',
      winter: 'Winter Serenity: Crisp Clear Air, Onsens & Snow-Capped Temples',
    },
    defaultStops: [
      {
        id: 'osaka',
        name: 'Osaka',
        country: 'Japan',
        nights: 2,
        role: 'Arrival Hub',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuD6mcxF54MPkKZuSc4IKenZHCkkj4fqa7VhihkWiSrZSkPj1t56XCkq7yA_tl7gobd3cqHYwesjfCWhbuSnaBjsalbEyub274sIagz887vs-R5V1iB3iguh3AgVFU2Na8y-oVAXvd7ZTFh_6fp-pPAcwYZ0jE-KK5YlQ3zBBwdfJKe0eYP_yShgXMqJMWF3SoOxSVBpPtTOW3lkx67sCW53IxFaw6Uo2gkmsYFVgoY0XcJCntKjZClZqw',
        imageAlt: 'Osaka Castle in Kansai Japan framed by autumn foliage',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~15 mins transit',
          title: 'Shinkansen Bullet Train',
        },
      },
      {
        id: 'kyoto',
        name: 'Kyoto',
        country: 'Japan',
        nights: 4,
        role: 'Cultural Core',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuC7oFD1Y3p6vCcjUmqwmAOb_fK7wWXF57RhOYK6kzWTwpaNN33T6XQHzLrPQMw9W8MGQnBB4cg1mUXt2qQ8EiFDW1q5VFZxZA4f0kK7VeQeKBhOBEDrUWMAPOvJVP4hzGrwk1kEE6bU6koP5oh7Uo1Af48-kSlbibY4htkykZy5XGGsNzfMal-K6Bznkf8Zm3y_U3YNSImP7fv1Mfi5nWCofJsvk-O8-H5Wr8YsHwkEkgDFTeTrImfCmw',
        imageAlt: 'Historic wooden machiya townhouses along stone-paved streets of Gion Kyoto',
        transitToNext: {
          mode: 'rail',
          icon: 'directions_railway',
          duration: '~2 hrs 10 mins',
          title: 'Thunderbird Express / Hokuriku Rail',
        },
      },
      {
        id: 'kanazawa',
        name: 'Kanazawa',
        country: 'Japan',
        nights: 4,
        role: 'Coastal Arts & Gardens',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuASGT2gtN2_fZnZAPe3e1Va6Nnw-HkAiXAZVcwts6ZinPOMGP64n0lw5Eg59yW54ssyg_za9aXdoBkk6w63NYlvo0Swe-kS17yGiNSPDqsRsH1dKbNUNtw8-MyonU7xIi6tKlgcHZGcNQ4ol4I53QiEL1dtxZi-ywcIKkXFs_s5hhjP-doYqSjsoQkmo3rRzpIrpt94dk5SCoij_3ayD4UN_pGZE5Ppg1pcbLZmyzIGTmQSMiy7UpLoOg',
        imageAlt: 'Kenroku-en garden in Kanazawa Japan featuring serene reflection pond',
      },
    ],
    suggestions: [
      {
        id: 'nara',
        name: 'Nara',
        region: 'Kansai, Japan',
        tag: '45m from Kyoto',
        description: 'Ancient imperial temples, tranquil gardens, and tame free-roaming sacred deer.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDmbrYV0nlJ9tj-8_4oy_u4VTjdxTQ7kdxlOYg6lpbzX5fytee4lVAMns8K7JhHt-P3wR2gJZg_mXPpKKbXiPJIxR1mTrvt0kjjxRvZIvlKIyWgnv6I4O8jmM_JGCqF7Ey1AjbSk7gZ_AAbJLi69FHFYer6nnShRzdeRElYugAj5rtszVd5S3gNMLPlmxGDJEhWZvbTE8C8HYkrS8euU--feI-a4GmdAMtuXDqnHIJMS8YIbVRtCKZx5w',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
      {
        id: 'hakone',
        name: 'Hakone & Mt. Fuji',
        region: 'Kanagawa, Japan',
        tag: 'Scenic Onsen Hub',
        description: 'Historic hot spring ryokans and dramatic caldera vistas across Lake Ashi.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuB2MuvkffHgjn_4kZ6l3pLmiOdUilTLO2YesCSddKEII6EdE7TntbeToA5RWIXVaQXZbS2lzBxf-AtJoxwHFgDYANduoDV3EbDWY1xDGsAeRk6_KQB75F0nmPMITU4pqJUu-lmZ9MIQAGgXqVQiT66Efm3olAqUNqReBxH8Uev2s85PyOVyJuVcedllqrfSvnDPANOJ81pLPhCt-hON5Q9jwDnnQ6Z_6dpzCKe2BEmiV-pBThkOv_jnZQ',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'hiroshima',
        name: 'Hiroshima & Miyajima',
        region: 'Chugoku, Japan',
        tag: 'Island & History',
        description: 'Moving Peace Memorial Park and iconic floating shrine on Miyajima Island.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBc2GF3n5qGVn4BiAQNRvX8goCk-kYrYgv6NhZvTZGfDkBdjZhmms6cLM6DPaSfZKR3t9H_5uRJK7h3sCOzARWJK99ijZWiLtYIBHyQhvwbt9bMNX-sAsCTCOXqiMVXgcNjMGEOoojSzy3EG6j4H-xZ4ZtQct5FqEK4dkQo3uoRFvFNvDNEIxwRkid6zAq2vdeTcEVBX0fuPhYvNDDOWVCSG4QSCttaCONyw5D0WYvFIzBxtXTunkPkbw',
        actionLabel: '+ Add Stop',
      },
    ],
  },
  {
    id: 'ladakh',
    name: 'Leh & Ladakh Circuit, India',
    alias: 'Ladakh Pass',
    scope: 'DOMESTIC',
    visaStatus: 'Domestic Trip • ₹0 Visa (ILP/PAP Required)',
    defaultDurationDays: 8,
    seasonInsights: {
      spring: 'Shoulder Season: Snowmelt Begins, Quiet Buddhist Monasteries',
      summer: 'Peak Season: High Mountain Passes Open, Pristine Turquoise Lakes',
      autumn: 'Golden Foliage: Golden Poplars Across Indus Valley, Crisp Air',
      winter: 'Winter Adventure: Sub-Zero Solitude, Chadar Frozen River Trek',
    },
    defaultStops: [
      {
        id: 'leh',
        name: 'Leh',
        country: 'India',
        nights: 3,
        role: 'High Altitude Hub',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuD7hvrOUblL6helHGgFAMcUR7U3EPEILzLqPeulKE-nxnyN2hEGNn1NwxlKcHvikC1FCWp3Xy6nzJJAOUlAp9KYFqtjZPn19ZCDnfyGduvwsMieGa4XfyW0pxhor-JXs0T2kog6xE0aUaNDVJA_fsT9QzASZs5_ZRXx8kxDwCNXz3yfm4Ume_eGePLT-Bai4ddfc8X-QSFjrpIwv9oS-ehMcl50MoJBYx41vx1c98ebFxJf3OP5226VQA',
        imageAlt: 'Leh palace and stupa against Himalayan mountains',
        transitToNext: {
          mode: 'drive',
          icon: 'directions_car',
          duration: '~4 hrs over Khardung La',
          title: 'Scenic Mountain Pass Highway',
        },
      },
      {
        id: 'nubra',
        name: 'Nubra Valley',
        country: 'India',
        nights: 2,
        role: 'Dune Valley & Monasteries',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCnRTowc0c7Auufma6M0HGK-QGaZPLV0vV7S5y8UPoWDYs8x6ngxcWlqDE2rm-kgBl1ZEj7jzkKHp0itJeOEBGEI8cIGF1WwjMLEaLHNtBplSrX5prNbP3SuwJQg4dP4_IdXwaNnrpckqmi1OkroYAFkT66Z2ZoAJpxmsKBsMsVg1U5bxy18HqnQ9-TUpEM_S8kzY9cqYA2G26J7eWp6t09a4fMHcwHystIbXkMlN2hw9Ym8KJdmEiBwA',
        imageAlt: 'Diskit monastery and sand dunes in Nubra Valley',
        transitToNext: {
          mode: 'drive',
          icon: 'directions_car',
          duration: '~5 hrs via Shyok Route',
          title: 'Shyok River Highland Route',
        },
      },
      {
        id: 'pangong',
        name: 'Pangong Tso',
        country: 'India',
        nights: 3,
        role: 'Glacial Sanctuary',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuAQOr-Jwi-E2Av5m4OSTPUCodU3aWEysFk_glFHIMNqIbIgsIu4r9JpTNOm1AMcI-oRuvNpSFLj1SPZPzd-SHVY552gvwNghsH9J674O9HBH4FJv-g3ly1PZ47t8ONFF8DTzg0oM6U81l5NlvhSo40oYZFOBrC6_zOV-8Lw7QBSJ1r2RAMngIdyIO1BUtJ9ZIZHQmQnA5HBI5JvAFYTRXj6MaGIdHDmlJk-lhFcd_V5y-S8uptO8u_ZYQ',
        imageAlt: 'Deep azure water of Pangong Tso surrounded by mountains',
      },
    ],
    suggestions: [
      {
        id: 'turtuk',
        name: 'Turtuk Border Village',
        region: 'Baltistan Border, Ladakh',
        tag: 'Balti Heritage',
        description: 'Historic apricot orchards, stone stone houses, and distinctive Balti culture.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDmbrYV0nlJ9tj-8_4oy_u4VTjdxTQ7kdxlOYg6lpbzX5fytee4lVAMns8K7JhHt-P3wR2gJZg_mXPpKKbXiPJIxR1mTrvt0kjjxRvZIvlKIyWgnv6I4O8jmM_JGCqF7Ey1AjbSk7gZ_AAbJLi69FHFYer6nnShRzdeRElYugAj5rtszVd5S3gNMLPlmxGDJEhWZvbTE8C8HYkrS8euU--feI-a4GmdAMtuXDqnHIJMS8YIbVRtCKZx5w',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'tso-moriri',
        name: 'Tso Moriri Lake',
        region: 'Changthang, Ladakh',
        tag: 'Remote Wetland Sanctuary',
        description: 'High-altitude protected wetland with migratory black-necked cranes.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuB2MuvkffHgjn_4kZ6l3pLmiOdUilTLO2YesCSddKEII6EdE7TntbeToA5RWIXVaQXZbS2lzBxf-AtJoxwHFgDYANduoDV3EbDWY1xDGsAeRk6_KQB75F0nmPMITU4pqJUu-lmZ9MIQAGgXqVQiT66Efm3olAqUNqReBxH8Uev2s85PyOVyJuVcedllqrfSvnDPANOJ81pLPhCt-hON5Q9jwDnnQ6Z_6dpzCKe2BEmiV-pBThkOv_jnZQ',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'alchi',
        name: 'Alchi & Likir Monasteries',
        region: 'Lower Ladakh',
        tag: 'Ancient Frescoes',
        description: '11th-century Kashmiri-influenced woodcarvings and clay Buddha sculptures.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBc2GF3n5qGVn4BiAQNRvX8goCk-kYrYgv6NhZvTZGfDkBdjZhmms6cLM6DPaSfZKR3t9H_5uRJK7h3sCOzARWJK99ijZWiLtYIBHyQhvwbt9bMNX-sAsCTCOXqiMVXgcNjMGEOoojSzy3EG6j4H-xZ4ZtQct5FqEK4dkQo3uoRFvFNvDNEIxwRkid6zAq2vdeTcEVBX0fuPhYvNDDOWVCSG4QSCttaCONyw5D0WYvFIzBxtXTunkPkbw',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'italy',
    name: 'Amalfi & Tuscany, Italy',
    alias: 'Italy Circuit',
    scope: 'INTERNATIONAL',
    visaStatus: 'Schengen Visa Required • ~15-30 Days Processing',
    defaultDurationDays: 12,
    seasonInsights: {
      spring: 'Optimal Season: Wildflowers Bloom Across Tuscan Hills & Mild Coasts',
      summer: 'Peak Summer: Sun-Drenched Mediterranean Coasts & Vibrant Piazzas',
      autumn: 'Optimal Season: Wine Harvest, Truffle Season & Golden Afternoon Light',
      winter: 'Low Season: Peaceful Classical Museums, Cosy Enoteche & Fewer Crowds',
    },
    defaultStops: [
      {
        id: 'rome',
        name: 'Rome',
        country: 'Italy',
        nights: 3,
        role: 'Imperial Gateway',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuAQOr-Jwi-E2Av5m4OSTPUCodU3aWEysFk_glFHIMNqIbIgsIu4r9JpTNOm1AMcI-oRuvNpSFLj1SPZPzd-SHVY552gvwNghsH9J674O9HBH4FJv-g3ly1PZ47t8ONFF8DTzg0oM6U81l5NlvhSo40oYZFOBrC6_zOV-8Lw7QBSJ1r2RAMngIdyIO1BUtJ9ZIZHQmQnA5HBI5JvAFYTRXj6MaGIdHDmlJk-lhFcd_V5y-S8uptO8u_ZYQ',
        imageAlt: 'Colosseum and historic Roman forum',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~1 hr 35 mins',
          title: 'Frecciarossa High-Speed Rail',
        },
      },
      {
        id: 'florence',
        name: 'Florence',
        country: 'Italy',
        nights: 4,
        role: 'Renaissance Heart',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCnRTowc0c7Auufma6M0HGK-QGaZPLV0vV7S5y8UPoWDYs8x6ngxcWlqDE2rm-kgBl1ZEj7jzkKHp0itJeOEBGEI8cIGF1WwjMLEaLHNtBplSrX5prNbP3SuwJQg4dP4_IdXwaNnrpckqmi1OkroYAFkT66Z2ZoAJpxmsKBsMsVg1U5bxy18HqnQ9-TUpEM_S8kzY9cqYA2G26J7eWp6t09a4fMHcwHystIbXkMlN2hw9Ym8KJdmEiBwA',
        imageAlt: 'Florence Duomo overlooking the terracotta roofs of Tuscany',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~2 hrs 50 mins',
          title: 'High-Speed Rail to Naples & Coastal Transfer',
        },
      },
      {
        id: 'positano',
        name: 'Positano & Amalfi',
        country: 'Italy',
        nights: 5,
        role: 'Coastal Cliff Sanctuary',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuAQOr-Jwi-E2Av5m4OSTPUCodU3aWEysFk_glFHIMNqIbIgsIu4r9JpTNOm1AMcI-oRuvNpSFLj1SPZPzd-SHVY552gvwNghsH9J674O9HBH4FJv-g3ly1PZ47t8ONFF8DTzg0oM6U81l5NlvhSo40oYZFOBrC6_zOV-8Lw7QBSJ1r2RAMngIdyIO1BUtJ9ZIZHQmQnA5HBI5JvAFYTRXj6MaGIdHDmlJk-lhFcd_V5y-S8uptO8u_ZYQ',
        imageAlt: 'Amalfi Coast pastel houses clinging to limestone cliffs',
      },
    ],
    suggestions: [
      {
        id: 'capri',
        name: 'Isle of Capri',
        region: 'Bay of Naples',
        tag: 'Sea Grotto Excursion',
        description: 'Limestone sea stacks, Blue Grotto boat passages, and scenic cliff trails.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDmbrYV0nlJ9tj-8_4oy_u4VTjdxTQ7kdxlOYg6lpbzX5fytee4lVAMns8K7JhHt-P3wR2gJZg_mXPpKKbXiPJIxR1mTrvt0kjjxRvZIvlKIyWgnv6I4O8jmM_JGCqF7Ey1AjbSk7gZ_AAbJLi69FHFYer6nnShRzdeRElYugAj5rtszVd5S3gNMLPlmxGDJEhWZvbTE8C8HYkrS8euU--feI-a4GmdAMtuXDqnHIJMS8YIbVRtCKZx5w',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
      {
        id: 'siena',
        name: 'Siena & Chianti',
        region: 'Tuscany',
        tag: 'Medieval Citadel',
        description: 'Gothic Piazza del Campo, rolling cypress hills, and private olive groves.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuB2MuvkffHgjn_4kZ6l3pLmiOdUilTLO2YesCSddKEII6EdE7TntbeToA5RWIXVaQXZbS2lzBxf-AtJoxwHFgDYANduoDV3EbDWY1xDGsAeRk6_KQB75F0nmPMITU4pqJUu-lmZ9MIQAGgXqVQiT66Efm3olAqUNqReBxH8Uev2s85PyOVyJuVcedllqrfSvnDPANOJ81pLPhCt-hON5Q9jwDnnQ6Z_6dpzCKe2BEmiV-pBThkOv_jnZQ',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'venice',
        name: 'Venice',
        region: 'Veneto',
        tag: 'Canal City',
        description: 'Serene gondola waterways, St. Mark’s Basilica, and historic palazzos.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBc2GF3n5qGVn4BiAQNRvX8goCk-kYrYgv6NhZvTZGfDkBdjZhmms6cLM6DPaSfZKR3t9H_5uRJK7h3sCOzARWJK99ijZWiLtYIBHyQhvwbt9bMNX-sAsCTCOXqiMVXgcNjMGEOoojSzy3EG6j4H-xZ4ZtQct5FqEK4dkQo3uoRFvFNvDNEIxwRkid6zAq2vdeTcEVBX0fuPhYvNDDOWVCSG4QSCttaCONyw5D0WYvFIzBxtXTunkPkbw',
        actionLabel: '+ Add Stop',
      },
    ],
  },
  {
    id: 'kerala',
    name: 'Kerala Backwaters & Coast, India',
    alias: 'Kerala Stays',
    scope: 'DOMESTIC',
    visaStatus: 'Domestic Trip • ₹0 Visa (No Passport Needed)',
    defaultDurationDays: 7,
    seasonInsights: {
      spring: 'Tropical Warmth: Serene Coastal Lagoons & Spice Plantation Breezes',
      summer: 'Tropical Pre-Monsoon: Warm Sunshine & Flowering Mango Groves',
      autumn: 'Monsoon Splendor: Verdant Backwaters & Ayurvedic Wellness',
      winter: 'Optimal Season: Crisp Coastal Evenings, Calm Houseboat Passages',
    },
    defaultStops: [
      {
        id: 'kochi',
        name: 'Fort Kochi',
        country: 'India',
        nights: 2,
        role: 'Colonial Maritime Port',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuD6mcxF54MPkKZuSc4IKenZHCkkj4fqa7VhihkWiSrZSkPj1t56XCkq7yA_tl7gobd3cqHYwesjfCWhbuSnaBjsalbEyub274sIagz887vs-R5V1iB3iguh3AgVFU2Na8y-oVAXvd7ZTFh_6fp-pPAcwYZ0jE-KK5YlQ3zBBwdfJKe0eYP_yShgXMqJMWF3SoOxSVBpPtTOW3lkx67sCW53IxFaw6Uo2gkmsYFVgoY0XcJCntKjZClZqw',
        imageAlt: 'Chinese fishing nets of Fort Kochi at sunset',
        transitToNext: {
          mode: 'drive',
          icon: 'directions_car',
          duration: '~3.5 hrs scenic ascent',
          title: 'Western Ghats Spice Route',
        },
      },
      {
        id: 'munnar',
        name: 'Munnar',
        country: 'India',
        nights: 3,
        role: 'Mist Tea Sanctuaries',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuASGT2gtN2_fZnZAPe3e1Va6Nnw-HkAiXAZVcwts6ZinPOMGP64n0lw5Eg59yW54ssyg_za9aXdoBkk6w63NYlvo0Swe-kS17yGiNSPDqsRsH1dKbNUNtw8-MyonU7xIi6tKlgcHZGcNQ4ol4I53QiEL1dtxZi-ywcIKkXFs_s5hhjP-doYqSjsoQkmo3rRzpIrpt94dk5SCoij_3ayD4UN_pGZE5Ppg1pcbLZmyzIGTmQSMiy7UpLoOg',
        imageAlt: 'Rolling green tea plantations of Munnar in morning mist',
        transitToNext: {
          mode: 'drive',
          icon: 'directions_car',
          duration: '~4 hrs descent to coast',
          title: 'Highland to Lagoon Transfer',
        },
      },
      {
        id: 'alleppey',
        name: 'Alleppey (Alappuzha)',
        country: 'India',
        nights: 2,
        role: 'Backwater Houseboat Trail',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuC7oFD1Y3p6vCcjUmqwmAOb_fK7wWXF57RhOYK6kzWTwpaNN33T6XQHzLrPQMw9W8MGQnBB4cg1mUXt2qQ8EiFDW1q5VFZxZA4f0kK7VeQeKBhOBEDrUWMAPOvJVP4hzGrwk1kEE6bU6koP5oh7Uo1Af48-kSlbibY4htkykZy5XGGsNzfMal-K6Bznkf8Zm3y_U3YNSImP7fv1Mfi5nWCofJsvk-O8-H5Wr8YsHwkEkgDFTeTrImfCmw',
        imageAlt: 'Traditional wooden houseboat navigating palm-fringed Kerala backwaters',
      },
    ],
    suggestions: [
      {
        id: 'varkala',
        name: 'Varkala Cliff',
        region: 'Kerala Coast',
        tag: 'Red Cliff & Arabian Sea',
        description: 'Red sandstone sea cliffs, quiet yoga sanctuaries, and coastal sunset cafes.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuAQOr-Jwi-E2Av5m4OSTPUCodU3aWEysFk_glFHIMNqIbIgsIu4r9JpTNOm1AMcI-oRuvNpSFLj1SPZPzd-SHVY552gvwNghsH9J674O9HBH4FJv-g3ly1PZ47t8ONFF8DTzg0oM6U81l5NlvhSo40oYZFOBrC6_zOV-8Lw7QBSJ1r2RAMngIdyIO1BUtJ9ZIZHQmQnA5HBI5JvAFYTRXj6MaGIdHDmlJk-lhFcd_V5y-S8uptO8u_ZYQ',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'thekkady',
        name: 'Thekkady & Periyar',
        region: 'Cardamom Hills',
        tag: 'Wildlife & Spices',
        description: 'Periyar lake boat safaris, elephant sanctuaries, and aromatic spice gardens.',
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuB2MuvkffHgjn_4kZ6l3pLmiOdUilTLO2YesCSddKEII6EdE7TntbeToA5RWIXVaQXZbS2lzBxf-AtJoxwHFgDYANduoDV3EbDWY1xDGsAeRk6_KQB75F0nmPMITU4pqJUu-lmZ9MIQAGgXqVQiT66Efm3olAqUNqReBxH8Uev2s85PyOVyJuVcedllqrfSvnDPANOJ81pLPhCt-hON5Q9jwDnnQ6Z_6dpzCKe2BEmiV-pBThkOv_jnZQ',
        actionLabel: '+ Add Stop',
      },
    ],
  },
];

export function getSeasonDescription(destinationStr: string, dateIsoStr: string): string {
  const date = new Date(dateIsoStr);
  const month = date.getMonth(); // 0 = Jan, 11 = Dec
  const destLower = destinationStr.toLowerCase();

  // Find matching circuit definition if available
  const circuit = PRECONFIGURED_CIRCUITS.find(
    (c) => destLower.includes(c.id) || destLower.includes(c.alias.toLowerCase())
  );

  let seasonKey = 'autumn';
  if (month >= 2 && month <= 4) seasonKey = 'spring';
  else if (month >= 5 && month <= 7) seasonKey = 'summer';
  else if (month >= 8 && month <= 10) seasonKey = 'autumn';
  else seasonKey = 'winter';

  if (circuit && circuit.seasonInsights[seasonKey]) {
    return circuit.seasonInsights[seasonKey];
  }

  // Fallbacks
  if (destLower.includes('ladakh') || destLower.includes('leh')) {
    return month >= 4 && month <= 8
      ? 'Optimal Season: High Mountain Passes Open & Crystal Skies'
      : 'Winter Adventure: Sub-Zero Climates & Frozen River Chadar Trails';
  }
  if (destLower.includes('japan') || destLower.includes('kyoto')) {
    return (month >= 8 && month <= 10) || (month >= 2 && month <= 4)
      ? 'Optimal Season: Pleasant Weather, Foliage & Mild Sunshine'
      : 'Favorable Season: Vibrant Cultural Atmosphere';
  }
  if (destLower.includes('kerala')) {
    return month >= 8 || month <= 2
      ? 'Optimal Season: Serene Coastal Weather & Houseboat Breezes'
      : 'Monsoon Splendor: Overflowing Waterfalls & Verdant Backwaters';
  }
  if (destLower.includes('italy')) {
    return month >= 3 && month <= 9
      ? 'Optimal Season: Mediterranean Sunshine & Pleasant Walking Temperatures'
      : 'Mild Winter: Quiet Art Sanctuaries & Fewer Crowds';
  }

  return 'Favorable Climate: Mild Temperatures & Pleasant Traveling Conditions';
}

export function getVisaVerdict(destinationStr: string): string {
  const destLower = destinationStr.toLowerCase();

  const circuit = PRECONFIGURED_CIRCUITS.find(
    (c) =>
      destLower.includes(c.id) ||
      destLower.includes(c.alias.toLowerCase()) ||
      destLower.includes(c.name.toLowerCase())
  );
  if (circuit) {
    return circuit.visaStatus;
  }

  if (
    destLower.includes('india') ||
    destLower.includes('ladakh') ||
    destLower.includes('leh') ||
    destLower.includes('kerala') ||
    destLower.includes('rajasthan') ||
    destLower.includes('goa') ||
    destLower.includes('jaipur')
  ) {
    return 'Domestic Trip • ₹0 Visa (No Passport Needed)';
  }
  if (destLower.includes('japan')) {
    return 'eVisa Active • 90 Days Single Entry for Indian Passports';
  }
  if (destLower.includes('italy') || destLower.includes('france') || destLower.includes('schengen')) {
    return 'Schengen Visa Required • ~15-30 Days Processing';
  }
  if (destLower.includes('indonesia') || destLower.includes('bali')) {
    return 'Visa on Arrival (e-VOA) • 30 Days Instant';
  }
  if (destLower.includes('thailand')) {
    return 'Visa Exemption / eVisa Available for Indian Passports';
  }
  return 'International Destination • Visa Guidance Active';
}
