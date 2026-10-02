import type {
  FinalItinerary,
  DayPlan,
  TransportLeg,
  DestinationDetail,
} from '../types/itinerary';

export const SAMPLE_DESTINATION_DETAILS: Record<string, DestinationDetail> = {
  Kyoto: {
    name: 'Kyoto',
    native_script: '京都',
    region: 'Kansai Region, Honshu',
    country: 'Japan',
    stop_number: 2,
    total_stops: 3,
    nights: 4,
    stay_dates: 'Oct 20–24, 2025',
    hero_image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuCG57e8ef7Xyy2U_WOF_V6Yle3aoPJ4Asru2sAhk_c8zp5Sp-rdBstMJQDzC1j1Rccj5fLCeQ0TMIXiT4psUkBWNH9ex-Qcdv1wEY8K4yZN0X78a-LRasqcop7xe-sCVjGBQVF2dgbSJZ5rWRfCzHl9NLdmTmOjnLAXvAkTwDflPCadNBP6RmZpFB83bhEjeWCyRjJ8H6Bd1h5aeBkyQe7NvMdfP6KG6Jgb8LDMThs13buRLLnux0JK0A',
    editorial_intro:
      'Ancient imperial capital for over a millennium, Kyoto holds the cultural heart of Japan. Here, moss-laden Zen rock gardens, morning temple bells, and preserved geiko preservation districts coalesce into an unhurried, contemplative cadence.',
    sanctuary_lodging_callout:
      'Anchored at Restored Gion Machiya Sanctuary for Days 03 through 06 with private maple tsuboniwa courtyard and Hinoki soaking baths.',
    snapshot: {
      recommended_stay: '4–5 Nights (Your Trip: 4 Nights)',
      seasonal_context: 'Peak Kōyō (Late Oct Maple Tint)',
      weather_context: '16°C High / 8°C Low (Crisp & Dry • 0% Rain)',
      currency_fx: 'Japanese Yen (~₹0.55 INR / ¥1 JPY)',
      language: 'Japanese (English signage across JR & Subway lines)',
      timezone: 'JST (UTC+9 • +3.5h ahead of IST)',
    },
    curator_selection: {
      quote:
        'Curated for travelers seeking unhurried aesthetic depth. Kyoto is sequenced as the contemplative center of your journey between Osaka’s gastronomic vigor and Kanazawa’s quiet craft guilds.',
      tags: ['Culture & Heritage (Primary)', 'Nature & Zen Landscapes', 'Artisanal Dining', 'Temple Architecture'],
      active_discovery_hours: 5.5,
      active_ratio_percent: 68,
      leisure_ratio_percent: 32,
    },
    neighborhoods: [
      {
        id: 'higashiyama',
        name: 'Higashiyama Historic Core',
        native_name: '東山区',
        description:
          'Preserved wooden machiya, stone-flagged pedestrian slopes, and atmospheric cedar temples leading to Kiyomizu-dera.',
        recommended_time: 'Dawn (06:30 – 08:30)',
        duration: '2.5 Hours',
        highlights: ['Ninenzaka & Sannenzaka Slopes', 'Yasaka Pagoda Vista', 'Otowa Sacred Spring'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCG57e8ef7Xyy2U_WOF_V6Yle3aoPJ4Asru2sAhk_c8zp5Sp-rdBstMJQDzC1j1Rccj5fLCeQ0TMIXiT4psUkBWNH9ex-Qcdv1wEY8K4yZN0X78a-LRasqcop7xe-sCVjGBQVF2dgbSJZ5rWRfCzHl9NLdmTmOjnLAXvAkTwDflPCadNBP6RmZpFB83bhEjeWCyRjJ8H6Bd1h5aeBkyQe7NvMdfP6KG6Jgb8LDMThs13buRLLnux0JK0A',
      },
      {
        id: 'gion',
        name: 'Gion Shirakawa & Pontocho',
        native_name: '祇園白川',
        description:
          'Quiet canal-side willow lanes by day and atmospheric lantern-lit geiko teahouse alleys by twilight.',
        recommended_time: 'Twilight (17:30 – 20:30)',
        duration: '2.0 Hours',
        highlights: ['Tatsumi Bridge', 'Kamogawa Riverfront', 'Kappo Counter Dining'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBL9JOQUkAr1UHWHX0MKx5vbG_xYKSlkYW4AbC9tkGkMEogf-1sN3yLQHATN2KI0sXypCMh4lMQrgHiS5DhoCLtb7sQhbq3y3jv-FyxUnlEmVifZA8x_FdsORAsFA_YkVd_DpNHSsxoyIYRD1e1Odl6vIQ4BJ0DACx-IYgdW6CbgGhAIOSJeW9ABf6ZjmDBmG32_PWUUS04pg0TKyNJIHFDoggINhMHOFHoTvvGC10Q0SD-iGCNVCRmVw',
      },
      {
        id: 'arashiyama',
        name: 'Arashiyama & Sagano Grove',
        native_name: '嵐山',
        description:
          'Soaring green bamboo groves, Tenryu-ji pond gardens, and wooden Togetsukyo bridge overlooking Oi River.',
        recommended_time: 'Early Morning (07:30 – 10:00)',
        duration: '3.0 Hours',
        highlights: ['Sagano Bamboo Forest', 'Tenryu-ji Zen Garden', 'Okochi Sanso Villa'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBN8A05kGXJJI6AmSXqUlBf3j1SAyGk10hS4t-FKrnzCkVF74fC_TJFz_kVHkqUQRYIy4fYTj7OrEnoAHExMw97n4bkxsJ7nmUDnfnf8Bm1SJFz-6YcuYICbZ1SlON4fQ1wxp8pxSnp8bocHaXWpyA2at_NDqH_nng9V3nbfnwAvGrnsr0hljDfC-UvzfeZRHZTh8_ZPtIeCydobYPUqXwIrIDFPXWGtldmJof5pyk-U69W_JzeiKy6rQ',
      },
      {
        id: 'fushimi',
        name: 'Fushimi & Southern Precincts',
        native_name: '伏見区',
        description:
          'Mountain shrine path lined with 10,000 vermilion torii gates and centuries-old sake breweries along Horikawa canal.',
        recommended_time: 'Late Afternoon (15:30 – 18:00)',
        duration: '2.5 Hours',
        highlights: ['Senbon Torii Path', 'Gekkeikan Okura Sake Museum', 'Mount Inari Overlook'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDYIhoNvkHAWligV8e5cXtEObIZzyZIFEDc90x349DWixd6W3pYOBUFfvnYwGWb3QDkjlkK_JJ5EzSKpyQOemvr8F-qhWAvhcSGJbDphQfcsi_FA6kk2N1Ka7LlcefASB6Yu6yoEi-oqPW5QLhsQ2AKukp4tcorle61RTMd_pkfDG-s2lsdgvR7ZPUqA39cVBIXm0E4infSMJDSDm_y-OW2eQ3XxUdzdtUGLCvGnuSedOxJ5szyCRH9TQ',
      },
    ],
    mobility_guide: {
      arrival_overview:
        'Tokaido Shinkansen bullet train from Shin-Osaka arrives at Kyoto Station in just 15 minutes. High frequency departures run every 7–10 minutes throughout the day.',
      local_transit:
        'Kyoto Station is the transit spine. Use Icoca/Suica IC smart card for seamless taps across Karasuma/Tozai subways and City Bus routes. MK Taxi is recommended for door-to-door morning temple arrivals.',
      walking_notes:
        'Kyoto’s historic core is best explored on foot. Comfortable slip-on shoes are essential for removing footwear at wooden temple verandas and tatami tea pavilions.',
    },
    next_stop: {
      destination: 'Kanazawa',
      transport_mode: 'EXPRESS_TRAIN',
      service_name: 'JR Thunderbird #17',
      duration: '2h 10m',
      leg_id: 'leg-3',
    },
  },
  Osaka: {
    name: 'Osaka',
    native_script: '大阪',
    region: 'Kansai Region, Honshu',
    country: 'Japan',
    stop_number: 1,
    total_stops: 3,
    nights: 2,
    stay_dates: 'Oct 18–20, 2025',
    hero_image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDYIhoNvkHAWligV8e5cXtEObIZzyZIFEDc90x349DWixd6W3pYOBUFfvnYwGWb3QDkjlkK_JJ5EzSKpyQOemvr8F-qhWAvhcSGJbDphQfcsi_FA6kk2N1Ka7LlcefASB6Yu6yoEi-oqPW5QLhsQ2AKukp4tcorle61RTMd_pkfDG-s2lsdgvR7ZPUqA39cVBIXm0E4infSMJDSDm_y-OW2eQ3XxUdzdtUGLCvGnuSedOxJ5szyCRH9TQ',
    editorial_intro:
      'Japan’s historic merchant kitchen. Dynamic, vibrant, and celebrated for culinary mastery, Osaka provides an energetic welcome into the Kansai corridor before slower temple rhythms in Kyoto.',
    sanctuary_lodging_callout:
      'Anchored at Boutique Design Hotel Osaka in Kuromon & Namba for Days 01 and 02 with curated dashi tastings and immediate market access.',
    snapshot: {
      recommended_stay: '2–3 Nights (Your Trip: 2 Nights)',
      seasonal_context: 'Mild Autumn Gastronomy Season',
      weather_context: '18°C High / 11°C Low (Sunny & Dry)',
      currency_fx: 'Japanese Yen (~₹0.55 INR / ¥1 JPY)',
      language: 'Japanese (Broad English in hotels & transit hubs)',
      timezone: 'JST (UTC+9 • +3.5h ahead of IST)',
    },
    curator_selection: {
      quote:
        'Chosen as your arrival gateway to ground you into Japanese hospitality through friendly counter dining, neon canals, and world-class street markets.',
      tags: ['Gastronomy & Street Food', 'Urban Energy', 'Historic Castle Grounds'],
      active_discovery_hours: 6.0,
      active_ratio_percent: 72,
      leisure_ratio_percent: 28,
    },
    neighborhoods: [
      {
        id: 'namba',
        name: 'Dotonbori & Namba',
        native_name: '道頓堀',
        description: 'Vibrant canal-side dining, neon signage, and hidden back-alley izakayas.',
        recommended_time: 'Evening (18:00 – 21:30)',
        duration: '3.0 Hours',
        highlights: ['Hozenji Yokocho Alleys', 'Canal Lantern Walk', 'Takoyaki Masters'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDYIhoNvkHAWligV8e5cXtEObIZzyZIFEDc90x349DWixd6W3pYOBUFfvnYwGWb3QDkjlkK_JJ5EzSKpyQOemvr8F-qhWAvhcSGJbDphQfcsi_FA6kk2N1Ka7LlcefASB6Yu6yoEi-oqPW5QLhsQ2AKukp4tcorle61RTMd_pkfDG-s2lsdgvR7ZPUqA39cVBIXm0E4infSMJDSDm_y-OW2eQ3XxUdzdtUGLCvGnuSedOxJ5szyCRH9TQ',
      },
    ],
    mobility_guide: {
      arrival_overview:
        'Kansai International Airport (KIX) is connected to central Osaka via Nankai Rapi:t express (34 mins to Namba) or JR Haruka Express.',
      local_transit: 'Osaka Metro Midosuji Line connects Umeda, Shinsaibashi, and Namba seamlessly.',
      walking_notes: 'Pedestrian-friendly arcades allow comfortable strolling regardless of autumn weather.',
    },
    next_stop: {
      destination: 'Kyoto',
      transport_mode: 'SHINKANSEN',
      service_name: 'Tokaido Shinkansen',
      duration: '15 mins',
      leg_id: 'leg-2',
    },
  },
  Kanazawa: {
    name: 'Kanazawa',
    native_script: '金沢',
    region: 'Hokuriku Region, Ishikawa',
    country: 'Japan',
    stop_number: 3,
    total_stops: 3,
    nights: 3,
    stay_dates: 'Oct 24–27, 2025',
    hero_image:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuBN8A05kGXJJI6AmSXqUlBf3j1SAyGk10hS4t-FKrnzCkVF74fC_TJFz_kVHkqUQRYIy4fYTj7OrEnoAHExMw97n4bkxsJ7nmUDnfnf8Bm1SJFz-6YcuYICbZ1SlON4fQ1wxp8pxSnp8bocHaXWpyA2at_NDqH_nng9V3nbfnwAvGrnsr0hljDfC-UvzfeZRHZTh8_ZPtIeCydobYPUqXwIrIDFPXWGtldmJof5pyk-U69W_JzeiKy6rQ',
    editorial_intro:
      'The jewel of the Sea of Japan coast. Unscathed by wartime conflicts, Kanazawa preserves authentic geisha and samurai quarters, celebrated gold leaf craftsmanship, and the peerless Kenroku-en garden.',
    sanctuary_lodging_callout:
      'Anchored at Coastal Heritage Ryokan & Onsen in Higashi Chaya for Days 07 through 09 with private outdoor hot springs and seasonal Echizen crab banquets.',
    snapshot: {
      recommended_stay: '3–4 Nights (Your Trip: 3 Nights)',
      seasonal_context: 'Crisp Coastal Autumn & Yukizuri Preparations',
      weather_context: '14°C High / 7°C Low (Light Coastal Mist • 15% Rain)',
      currency_fx: 'Japanese Yen (~₹0.55 INR / ¥1 JPY)',
      language: 'Japanese (Good tourist services at Kanazawa Station)',
      timezone: 'JST (UTC+9 • +3.5h ahead of IST)',
    },
    curator_selection: {
      quote:
        'Sequenced as your restorative finale. Kanazawa offers world-class artisanal immersion without the tourist crowds of the central Pacific corridor.',
      tags: ['Artisanal Crafts & Gold Leaf', 'Classical Strolling Gardens', 'Sea of Japan Seafood'],
      active_discovery_hours: 5.0,
      active_ratio_percent: 65,
      leisure_ratio_percent: 35,
    },
    neighborhoods: [
      {
        id: 'higashichaya',
        name: 'Higashi Chaya District',
        native_name: 'ひがし茶屋街',
        description: 'Latticed two-story wooden teahouses where geiko performances and gold leaf studios thrive.',
        recommended_time: 'Afternoon (14:00 – 17:00)',
        duration: '2.5 Hours',
        highlights: ['Hakuichi Gold Leaf Atelier', 'Shima Geisha Museum', 'Wagashi Confectionery'],
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBN8A05kGXJJI6AmSXqUlBf3j1SAyGk10hS4t-FKrnzCkVF74fC_TJFz_kVHkqUQRYIy4fYTj7OrEnoAHExMw97n4bkxsJ7nmUDnfnf8Bm1SJFz-6YcuYICbZ1SlON4fQ1wxp8pxSnp8bocHaXWpyA2at_NDqH_nng9V3nbfnwAvGrnsr0hljDfC-UvzfeZRHZTh8_ZPtIeCydobYPUqXwIrIDFPXWGtldmJof5pyk-U69W_JzeiKy6rQ',
      },
    ],
    mobility_guide: {
      arrival_overview:
        'JR Thunderbird Express runs directly along Lake Biwa from Kyoto to Tsuruga/Kanazawa in 2h 10m. Station features architectural Tsuzumi-mon wooden gate.',
      local_transit: 'Kanazawa Loop Bus circles Kenroku-en, 21st Century Museum, and Chaya districts every 15 minutes.',
      walking_notes: 'Compact city center easily traversed on foot; carry a compact umbrella for coastal showers.',
    },
    next_stop: {
      destination: 'Tokyo / Departure Gateway',
      transport_mode: 'HOKURIKU_SHINKANSEN',
      service_name: 'Kagayaki Shinkansen',
      duration: '2h 28m',
      leg_id: 'leg-4',
    },
  },
};

export const SAMPLE_HOKURIKU_ITINERARY: FinalItinerary = {
  trip_id: 'SF-8492',
  title: 'Autumn Along the Hokuriku Corridor',
  summary:
    'An unhurried 10-day expedition balancing historic machiya sanctuaries, quiet morning temple paths, and artisanal craft guilds across Osaka, Kyoto, and Kanazawa.',
  curator_note:
    'We have structured this journey around unhurried morning transitions, avoiding mid-day temple rush hours and timing your arrival in Kyoto to coincide with peak maple foliage in the Higashiyama hills. Rail transfers are linked via JR Green Car segments with seamless forward luggage delivery from Osaka to Kanazawa.',
  cover_image: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCG57e8ef7Xyy2U_WOF_V6Yle3aoPJ4Asru2sAhk_c8zp5Sp-rdBstMJQDzC1j1Rccj5fLCeQ0TMIXiT4psUkBWNH9ex-Qcdv1wEY8K4yZN0X78a-LRasqcop7xe-sCVjGBQVF2dgbSJZ5rWRfCzHl9NLdmTmOjnLAXvAkTwDflPCadNBP6RmZpFB83bhEjeWCyRjJ8H6Bd1h5aeBkyQe7NvMdfP6KG6Jgb8LDMThs13buRLLnux0JK0A',
    alt: 'Autumn in Ninenzaka Kyoto lane',
    waypoint_title: 'Historic Ninenzaka lane at dawn, Kyoto',
    stay_highlight: 'Confirmed Stay: Traditional Gion Machiya sanctuary with private maple tsuboniwa courtyard.',
    seasonal_badge: 'Autumn Foliage Peak Season (Kōyō) • Kansai & Hokuriku',
  },
  pace_rhythm_index: {
    cultural_immersiveness: 94,
    transit_leisure_margin: 88,
    vetted_by: 'Senior Destination Architect',
  },
  trip_context: {
    origin: 'New Delhi (DEL)',
    destinations: ['Osaka', 'Kyoto', 'Kanazawa'],
    start_date: 'Oct 18, 2025',
    end_date: 'Oct 28, 2025',
    duration_days: 10,
    budget_inr: 380000,
    num_travelers: 2,
    travel_style: 'COMFORTABLE',
    pace: 'BALANCED',
    scope: 'INTERNATIONAL',
  },
  logistics_plan: {
    transport_legs: [
      {
        id: 'leg-1',
        origin: 'New Delhi (DEL)',
        destination: 'Osaka (KIX)',
        mode: 'FLIGHT',
        operator: 'Direct International Corridor',
        service_name: 'Air India / ANA International 308',
        carrier: 'All Nippon Airways',
        duration: '7h 45m',
        cost_inr: 45000,
        travel_date: 'Sat, Oct 18, 2025',
        distance_km: 5850,
        notes: 'Overnight transit · direct terminal clearance',
        seat_reservation: 'Row 14, Premium Window Alignment',
        pass_coverage: 'Direct ticket issued',
      },
      {
        id: 'leg-2',
        origin: 'Osaka (Umeda / Shin-Osaka)',
        destination: 'Kyoto Station',
        mode: 'SHINKANSEN',
        operator: 'Tokaido Shinkansen',
        service_name: 'Nozomi Bullet Rail #214',
        carrier: 'JR Central',
        equipment: 'N700S Series Shinkansen',
        duration: '15 min bullet rail',
        cost_inr: 2800,
        travel_date: 'Mon, Oct 20, 2025',
        distance_km: 43.8,
        notes: 'Frequent departures every 10 mins',
        seat_reservation: 'Car 09, Reserved Green Seats',
        pass_coverage: 'Covered under JR Hokuriku Arch Pass',
      },
      {
        id: 'leg-3',
        origin: 'Kyoto Station',
        destination: 'Kanazawa Station',
        mode: 'TRAIN',
        operator: 'JR Thunderbird Express / Shinkansen',
        service_name: 'JR Thunderbird #17',
        carrier: 'JR West (West Japan Railway Company)',
        equipment: '683 Series Limited Express EMU',
        seat_reservation: 'Car 01, Seats 4A & 4B (Forward Facing, Lake View)',
        luggage_policy:
          'Hands-free travel protocol: Main baggage forwarded via Yamato Transport directly from Gion Machiya to Kanazawa Ryokan. Travel with light daypack only.',
        pass_coverage: 'Fully covered under JR Hokuriku Arch Pass & Japan Rail National Pass',
        travel_date: 'Fri, Oct 24, 2025',
        duration: '2h 10m scenic lakeside',
        distance_km: 218.4,
        cost_inr: 6500,
        notes: 'Scenic Lake Biwa route with forward luggage dispatch',
        fare_breakdown: {
          base_fare_inr: 3850,
          seat_reservation_inr: 2650,
          currency_local: 'JPY',
          total_local: '¥11,800',
          status: 'Included in Curated Pass Package',
        },
        milestones: [
          {
            time: '09:15',
            label: 'Sanctuary Departure',
            location: 'Gion Shirakawa Machiya Inn',
            description:
              'Main bags handed to Yamato Transport forward courier; MK private taxi transfer to Kyoto Station (15 min transit buffer).',
            icon: 'hotel',
            status: 'completed',
          },
          {
            time: '09:40',
            label: 'Station Check-in & Bento Pick',
            location: 'Kyoto Station Platform 0',
            description:
              'Trackside arrival at Platform 0; artisanal seasonal ekiben bento selected from Station Promenade atelier.',
            icon: 'train',
            status: 'completed',
          },
          {
            time: '10:09 ➔ 12:19',
            label: 'Active Express Corridor',
            location: 'JR Thunderbird #17 (Green Car 01)',
            description:
              'Lake Biwa western shoreline vistas from right-side panoramic windows. Smooth transit traversing Shiga & Fukui mountains.',
            icon: 'directions_railway',
            status: 'active',
          },
          {
            time: '12:19',
            label: 'Terminus Arrival',
            location: 'Kanazawa Station (Tsuzumi-mon Gate)',
            description:
              'Arrival beneath the grand wooden Tsuzumi gate; seamless Hokuriku bus connection or 8 min taxi to Higashi Chaya.',
            icon: 'location_on',
            status: 'upcoming',
          },
          {
            time: '12:45',
            label: 'Sanctuary Check-in',
            location: 'Coastal Heritage Ryokan in Higashi Chaya',
            description:
              'Welcome matcha tea ceremony and room orientation; forwarded luggage verified safely delivered in guest chambers.',
            icon: 'spa',
            status: 'upcoming',
          },
        ],
        intermediate_stops: [
          { station: 'Kyoto Station', time: '10:09 Dep', platform: 'Platform 0', notes: 'Origin Departure' },
          { station: 'Omi-Imazu', time: '10:48', notes: 'Lake Biwa Scenic Turn' },
          { station: 'Tsuruga', time: '11:21', notes: 'Hokuriku Mountain Pass Entry' },
          { station: 'Fukui', time: '11:42', platform: 'Platform 2', notes: 'Echizen Craft Region' },
          { station: 'Komatsu', time: '12:04', notes: 'Kutani Ceramics Valley' },
          { station: 'Kanazawa Station', time: '12:19 Arr', platform: 'Platform 1', notes: 'Terminus Gate' },
        ],
      },
    ],
    hotel_stays: [
      {
        id: 'stay-1',
        hotel_name: 'Boutique Design Hotel Osaka',
        city: 'Osaka',
        check_in: 'Oct 18, 2025',
        check_out: 'Oct 20, 2025',
        nights: 2,
        cost_inr: 28000,
        neighborhood: 'Kuromon & Namba',
        style: 'Modern Boutique',
        confirmed: true,
      },
      {
        id: 'stay-2',
        hotel_name: 'Restored Gion Machiya Sanctuary',
        city: 'Kyoto',
        check_in: 'Oct 20, 2025',
        check_out: 'Oct 24, 2025',
        nights: 4,
        cost_inr: 78000,
        neighborhood: 'Gion Shirakawa',
        style: 'Heritage Townhouse Ryokan',
        confirmed: true,
      },
      {
        id: 'stay-3',
        hotel_name: 'Coastal Heritage Ryokan & Onsen',
        city: 'Kanazawa',
        check_in: 'Oct 24, 2025',
        check_out: 'Oct 27, 2025',
        nights: 3,
        cost_inr: 36000,
        neighborhood: 'Higashi Chaya',
        style: 'Artisanal Ryokan',
        confirmed: true,
      },
    ],
    total_transport_cost_inr: 94800,
    total_accommodation_cost_inr: 142000,
  },
  experience_plan: {
    total_days: 10,
    days: [
      {
        day_number: 1,
        date: 'Sat, Oct 18, 2025',
        city: 'Osaka',
        theme: 'Arrival & Gastronomic Introduction',
        activities: [
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Kuromon Market & Namba Orientation',
              category: 'FOOD_EXPERIENCE',
              city: 'Osaka',
              estimated_cost_inr: 2500,
              description: 'Gastronomy walk sampling seasonal street delicacies.',
            },
          },
          {
            daypart: 'EVENING',
            poi: {
              name: 'Dotonbori Lantern Walk',
              category: 'LOCAL_EXPERIENCE',
              city: 'Osaka',
              estimated_cost_inr: 1500,
              description: 'Unhurried dusk walk through ambient canal-side alleys.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'DINNER',
            name: 'Secret Alleyway Takoyaki & Seasonal Dashi Broths',
            cuisine: 'Japanese Kappo & Street Cuisine',
            estimated_cost_inr: 3200,
            restaurant_name: 'Dotonbori Backstreet Atelier',
          },
        ],
        metrics: {
          active_hours: 4.5,
          rest_hours: 3.5,
          walking_steps: 6800,
          walking_km: 5.1,
          pacing_label: 'Gentle Arrival Cadence',
        },
        weather_forecast: {
          condition: 'Sunny / Dry',
          temp_celsius: 18,
          temp_high_celsius: 20,
          temp_low_celsius: 12,
          precipitation_chance: 0,
          advisory: 'Pleasant evening temperatures for canal strolls.',
        },
        stay: {
          name: 'Boutique Design Hotel Osaka',
          type: 'Boutique Hotel',
          neighborhood: 'Kuromon & Namba',
          cost_inr: 14000,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 4000,
          meals_inr: 4500,
          transit_inr: 800,
          stays_inr: 14000,
          total_inr: 23300,
        },
        next_day_teaser: {
          day_number: 2,
          theme: 'Osaka Castle Parkland & Shinsekai Retro Alleys',
          city: 'Osaka',
        },
      },
      {
        day_number: 2,
        date: 'Sun, Oct 19, 2025',
        city: 'Osaka',
        theme: 'Osaka Castle Parkland & Shinsekai Retro Alleys',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Osaka Castle Dawn Park & Ote-mon Gate',
              category: 'HISTORY_HERITAGE',
              city: 'Osaka',
              estimated_cost_inr: 1200,
              description: 'Gentle stroll through massive stone ramparts and moat reflections before midday visitors.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Shinsekai & Tsutenkaku Heritage Walk',
              category: 'LOCAL_EXPERIENCE',
              city: 'Osaka',
              estimated_cost_inr: 2200,
              description: 'Retro 1920s nostalgia alleys with artisan workshop visits.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Artisanal Kushikatsu Tasting',
            cuisine: 'Osaka Kushikatsu',
            estimated_cost_inr: 2800,
            restaurant_name: 'Daruma Shinsekai',
          },
          {
            meal_type: 'DINNER',
            name: 'Handcrafted Udon & Seasonal Tempura',
            cuisine: 'Kansai Udon',
            estimated_cost_inr: 2400,
            restaurant_name: 'Dotonbori Imai',
          },
        ],
        metrics: {
          active_hours: 5.0,
          rest_hours: 3.0,
          walking_steps: 7900,
          walking_km: 5.8,
          pacing_label: 'Balanced Discovery',
        },
        weather_forecast: {
          condition: 'Clear Skies',
          temp_celsius: 19,
          temp_high_celsius: 21,
          temp_low_celsius: 13,
          precipitation_chance: 0,
          advisory: 'Clear sunny day; excellent visibility across castle moats.',
        },
        stay: {
          name: 'Boutique Design Hotel Osaka',
          type: 'Boutique Hotel',
          neighborhood: 'Kuromon & Namba',
          cost_inr: 14000,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 3400,
          meals_inr: 5200,
          transit_inr: 900,
          stays_inr: 14000,
          total_inr: 23500,
        },
        next_day_teaser: {
          day_number: 3,
          theme: 'Sacred Dawn, Gion Whispers & Zen Sanctuary',
          city: 'Kyoto',
        },
      },
      {
        day_number: 3,
        date: 'Mon, Oct 20, 2025',
        city: 'Kyoto',
        theme: 'Sacred Dawn, Gion Whispers & Zen Sanctuary',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Quiet Dawn Walk: Ninenzaka & Sannenzaka Slopes',
              category: 'HISTORY_HERITAGE',
              city: 'Kyoto',
              estimated_cost_inr: 1800,
              description: 'Ascent to Kiyomizu-dera via preservation alleyways before daytime tour groups.',
              is_must_visit: true,
            },
            notes: 'Uncrowded window: early access before 08:30 ensures pristine stone-lane photography.',
          },
          {
            daypart: 'MORNING',
            poi: {
              name: 'Private Dawn Tea Ritual at Nanzen-ji Sub-temple',
              category: 'SPIRITUAL',
              city: 'Kyoto',
              estimated_cost_inr: 4500,
              description:
                'Uncrowded garden contemplation before general gates open. A 16th-generation tea master introduces morning matcha and seasonal wagashi.',
              is_must_visit: true,
            },
            notes: 'Private access voucher confirmed. Remove footwear at cedar engawa veranda.',
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Gion Shirakawa Artisanal Silk Atelier & Preservation Canal Walk',
              category: 'LOCAL_EXPERIENCE',
              city: 'Kyoto',
              estimated_cost_inr: 2400,
              description:
                'Direct engagement with traditional Kyoto kimono silk weavers and lacquerware masters along the weeping willows of Shirakawa canal.',
            },
            notes: 'Includes hands-on silk screening preview at heritage machiya studio.',
          },
          {
            daypart: 'EVENING',
            poi: {
              name: 'Twilight Lantern Walk Along Pontocho Alley',
              category: 'LOCAL_EXPERIENCE',
              city: 'Kyoto',
              estimated_cost_inr: 1500,
              description:
                'Atmospheric dusk stroll along the Kamogawa riverbank lit by traditional washi lanterns and heritage teahouse entrances.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Seasonal Kaiseki Multi-Course',
            cuisine: 'Kyoto Kaiseki',
            estimated_cost_inr: 5800,
            restaurant_name: 'Gion Karyo',
            notes: 'Reserved tatami room with seasonal autumn momiji presentation.',
          },
          {
            meal_type: 'DINNER',
            name: 'Kappo Counter Dining at Gion Owatari',
            cuisine: 'Seasonal Kyoto Kappo',
            estimated_cost_inr: 6400,
            restaurant_name: 'Gion Owatari',
            notes: 'Direct 8-seat counter interaction with master chef.',
          },
        ],
        weather_forecast: {
          condition: 'Crisp Autumn',
          temp_celsius: 16,
          temp_high_celsius: 18,
          temp_low_celsius: 8,
          precipitation_chance: 0,
          advisory: 'Optimal morning lighting for Ninenzaka slopes; slip-on shoes recommended for temple tatami.',
          icon: 'park',
        },
        stay: {
          name: 'Restored Gion Machiya Sanctuary',
          type: 'Heritage Townhouse Ryokan',
          neighborhood: 'Gion Shirakawa',
          cost_inr: 19500,
          confirmed: true,
          check_in: '15:00',
          amenities: ['Hinoki Wood Soaking Bath', 'Private Tsuboniwa Garden', 'Matcha Welcome Ceremony', 'Yamato Luggage Drop'],
        },
        metrics: {
          active_hours: 5.5,
          rest_hours: 2.5,
          walking_steps: 8400,
          walking_km: 6.2,
          pacing_label: 'Balanced & Meditative',
        },
        featured_experience: {
          title: 'Quiet Dawn Walk: Ninenzaka & Sannenzaka Slopes',
          subtitle: 'Ascent to Kiyomizu-dera via preservation alleyways before daytime tour groups.',
          time_window: '06:45 – 08:30 (1h 45m Leisurely Stroll)',
          duration: '1h 45m',
          image_url:
            'https://lh3.googleusercontent.com/aida-public/AB6AXuCG57e8ef7Xyy2U_WOF_V6Yle3aoPJ4Asru2sAhk_c8zp5Sp-rdBstMJQDzC1j1Rccj5fLCeQ0TMIXiT4psUkBWNH9ex-Qcdv1wEY8K4yZN0X78a-LRasqcop7xe-sCVjGBQVF2dgbSJZ5rWRfCzHl9NLdmTmOjnLAXvAkTwDflPCadNBP6RmZpFB83bhEjeWCyRjJ8H6Bd1h5aeBkyQe7NvMdfP6KG6Jgb8LDMThs13buRLLnux0JK0A',
          tags: ['Peak Kōyō Foliage', 'Window of Utmost Quietude', 'Confirmed Route'],
          why_included:
            'Ninenzaka and Sannenzaka represent the architectural soul of ancient Kyoto. Experiencing these stone-flagged lanes at dawn bypasses the 20,000 daily midday visitors, allowing the resonant toll of temple bells and early temple monks sweepings to set the emotional tempo of your Kyoto residency.',
          curator_tips: [
            'Arrive at the Yasaka Pagoda view framing spot by 07:05 for optimum soft autumn morning light.',
            'The steep stone steps of Sannenzaka can be damp with morning dew; wear supportive, slip-resistant walking shoes.',
            'Follow the quiet northern path toward Maruyama Park for an undisturbed return trail.',
          ],
          transit_connection: '8 min unhurried walk from Gion Shirakawa Machiya Sanctuary',
        },
        hourly_atmosphere: [
          { time: '06:00', temp: '11°C', condition: 'Dawn Mist', precipitation: '0%', icon: 'wb_twilight' },
          { time: '09:00', temp: '14°C', condition: 'Crisp Sun', precipitation: '0%', icon: 'sunny' },
          { time: '12:00', temp: '17°C', condition: 'Warm Autumn', precipitation: '0%', icon: 'sunny' },
          { time: '15:00', temp: '16°C', condition: 'Golden Light', precipitation: '0%', icon: 'light_mode' },
          { time: '18:00', temp: '13°C', condition: 'Evening Breeze', precipitation: '0%', icon: 'air' },
          { time: '21:00', temp: '10°C', condition: 'Clear Chill', precipitation: '0%', icon: 'bedtime' },
        ],
        day_budget: {
          activities_inr: 6300,
          meals_inr: 12200,
          transit_inr: 1200,
          stays_inr: 19500,
          total_inr: 39200,
        },
        next_day_teaser: {
          day_number: 4,
          theme: 'Arashiyama Sagano Bamboo Path & Tenryu-ji Zen Waters',
          city: 'Kyoto',
        },
      },
      {
        day_number: 4,
        date: 'Tue, Oct 21, 2025',
        city: 'Kyoto',
        theme: 'Arashiyama Sagano Bamboo Path & Tenryu-ji Zen Waters',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Sagano Bamboo Forest Dawn Whisper',
              category: 'NATURE',
              city: 'Kyoto',
              estimated_cost_inr: 900,
              description: 'Early morning tranquility along towering jade stalks before midday tourist flow.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Tenryu-ji World Heritage Sogenchi Garden',
              category: 'SPIRITUAL',
              city: 'Kyoto',
              estimated_cost_inr: 1800,
              description: '14th-century pond garden framed by vibrant maple mountain backdrops.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Shigetsu Temple Buddhist Vegetarian Shojin Ryori',
            cuisine: 'Shojin Ryori',
            estimated_cost_inr: 4200,
            restaurant_name: 'Shigetsu',
          },
          {
            meal_type: 'DINNER',
            name: 'Kamo Riverbank Charcoal Robatayaki',
            cuisine: 'Robatayaki',
            estimated_cost_inr: 3800,
            restaurant_name: 'Gion Nanba',
          },
        ],
        metrics: {
          active_hours: 5.5,
          rest_hours: 2.5,
          walking_steps: 9200,
          walking_km: 6.8,
          pacing_label: 'Meditative Nature Immersion',
        },
        weather_forecast: {
          condition: 'Crisp Sun',
          temp_celsius: 17,
          temp_high_celsius: 19,
          temp_low_celsius: 9,
          precipitation_chance: 0,
          advisory: 'Dry and sunny; gentle wind in bamboo stalks.',
        },
        stay: {
          name: 'Restored Gion Machiya Sanctuary',
          type: 'Heritage Townhouse Ryokan',
          neighborhood: 'Gion Shirakawa',
          cost_inr: 19500,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 2700,
          meals_inr: 8000,
          transit_inr: 1400,
          stays_inr: 19500,
          total_inr: 31600,
        },
        next_day_teaser: {
          day_number: 5,
          theme: 'Philosopher’s Path, Ginkaku-ji & Zen Calligraphy',
          city: 'Kyoto',
        },
      },
      {
        day_number: 5,
        date: 'Wed, Oct 22, 2025',
        city: 'Kyoto',
        theme: 'Philosopher’s Path, Ginkaku-ji & Zen Calligraphy',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Ginkaku-ji Silver Pavilion & Sand Garden',
              category: 'HISTORY_HERITAGE',
              city: 'Kyoto',
              estimated_cost_inr: 1500,
              description: 'Iconic Kogetsudai sand cone and moss-covered garden trails.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Private Washi Paper & Calligraphy Atelier',
              category: 'LOCAL_EXPERIENCE',
              city: 'Kyoto',
              estimated_cost_inr: 3500,
              description: 'Hands-on brushwork workshop with master calligrapher along the canal.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Handcrafted Soba in Sukiya Pavilion',
            cuisine: 'Kyoto Soba',
            estimated_cost_inr: 2400,
            restaurant_name: 'Omen Ginkakuji',
          },
          {
            meal_type: 'DINNER',
            name: 'Kyoto Yuba & Tofu Tasting Feast',
            cuisine: 'Tofu Kaiseki',
            estimated_cost_inr: 4500,
            restaurant_name: 'Tousuiro Kiyamachi',
          },
        ],
        metrics: {
          active_hours: 5.0,
          rest_hours: 3.0,
          walking_steps: 8100,
          walking_km: 5.9,
          pacing_label: 'Artisanal Contemplation',
        },
        weather_forecast: {
          condition: 'Partly Sunny',
          temp_celsius: 16,
          temp_high_celsius: 18,
          temp_low_celsius: 8,
          precipitation_chance: 5,
          advisory: 'Ideal conditions for stone path canal walks.',
        },
        stay: {
          name: 'Restored Gion Machiya Sanctuary',
          type: 'Heritage Townhouse Ryokan',
          neighborhood: 'Gion Shirakawa',
          cost_inr: 19500,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 5000,
          meals_inr: 6900,
          transit_inr: 1100,
          stays_inr: 19500,
          total_inr: 32500,
        },
        next_day_teaser: {
          day_number: 6,
          theme: 'Fushimi Inari Torii Paths & Historic Sake Cellars',
          city: 'Kyoto',
        },
      },
      {
        day_number: 6,
        date: 'Thu, Oct 23, 2025',
        city: 'Kyoto',
        theme: 'Fushimi Inari Torii Paths & Historic Sake Cellars',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Fushimi Inari-Taisha Sacred Mountain Ascent',
              category: 'SPIRITUAL',
              city: 'Kyoto',
              estimated_cost_inr: 1000,
              description: 'Hiking beneath 10,000 vermilion torii gates to the Yotsutsuji intersection overlook.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Gekkeikan Okura Sake Brewery & Tasting',
              category: 'FOOD_EXPERIENCE',
              city: 'Kyoto',
              estimated_cost_inr: 2500,
              description: 'Tasting rare junmai daiginjo brewed with pristine Fushimi spring water.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Local Fushimi Inari Sushi & Kitsune Udon',
            cuisine: 'Traditional Kansai',
            estimated_cost_inr: 2200,
            restaurant_name: 'Nezameya',
          },
          {
            meal_type: 'DINNER',
            name: 'Kyoto Duck Hotpot (Kamo Nabe)',
            cuisine: 'Kyoto Hotpot',
            estimated_cost_inr: 5200,
            restaurant_name: 'Toriyasu',
          },
        ],
        metrics: {
          active_hours: 6.0,
          rest_hours: 2.0,
          walking_steps: 11200,
          walking_km: 8.1,
          pacing_label: 'Active Mountain Pilgrimage',
        },
        weather_forecast: {
          condition: 'Crisp & Clear',
          temp_celsius: 15,
          temp_high_celsius: 17,
          temp_low_celsius: 7,
          precipitation_chance: 0,
          advisory: 'Mountain paths can be chilly in early morning shadows.',
        },
        stay: {
          name: 'Restored Gion Machiya Sanctuary',
          type: 'Heritage Townhouse Ryokan',
          neighborhood: 'Gion Shirakawa',
          cost_inr: 19500,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 3500,
          meals_inr: 7400,
          transit_inr: 1500,
          stays_inr: 19500,
          total_inr: 31900,
        },
        next_day_teaser: {
          day_number: 7,
          theme: 'Scenic Lake Biwa Rail Transit to Kanazawa Coast',
          city: 'Kanazawa',
        },
      },
      {
        day_number: 7,
        date: 'Fri, Oct 24, 2025',
        city: 'Kanazawa',
        theme: 'Scenic Lake Biwa Rail Transit to Kanazawa Coast',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'JR Thunderbird #17 Scenic Lake Biwa Rail Journey',
              category: 'LOCAL_EXPERIENCE',
              city: 'Kyoto to Kanazawa',
              estimated_cost_inr: 6500,
              description: 'Panoramic rail transfer across the western shore of Lake Biwa into Ishikawa prefecture.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Higashi Chaya Historic Preservation District Orientation',
              category: 'HISTORY_HERITAGE',
              city: 'Kanazawa',
              estimated_cost_inr: 1200,
              description: 'Afternoon stroll amidst 19th-century wooden teahouse facades and gold leaf boutiques.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Curated Kyoto Station Autumn Bento on Rail',
            cuisine: 'Ekiben Bento',
            estimated_cost_inr: 2200,
            restaurant_name: 'Kyoto Station Promenade',
          },
          {
            meal_type: 'DINNER',
            name: 'Seasonal Kanazawa Kaiseki with Sea of Japan Crab',
            cuisine: 'Kaga Kaiseki',
            estimated_cost_inr: 7500,
            restaurant_name: 'Ryokan Chousen',
          },
        ],
        metrics: {
          active_hours: 4.0,
          rest_hours: 4.0,
          walking_steps: 6200,
          walking_km: 4.4,
          pacing_label: 'Scenic Transit & Restorative Onsen',
        },
        weather_forecast: {
          condition: 'Cool Coastal Air',
          temp_celsius: 14,
          temp_high_celsius: 16,
          temp_low_celsius: 8,
          precipitation_chance: 10,
          advisory: 'Gentle coastal breeze; enjoy evening Hinoki soaking bath.',
        },
        stay: {
          name: 'Coastal Heritage Ryokan & Onsen',
          type: 'Artisanal Ryokan',
          neighborhood: 'Higashi Chaya',
          cost_inr: 12000,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 7700,
          meals_inr: 9700,
          transit_inr: 800,
          stays_inr: 12000,
          total_inr: 30200,
        },
        next_day_teaser: {
          day_number: 8,
          theme: 'Kenroku-en Gardens & Ancient Artisanal Chaya Guilds',
          city: 'Kanazawa',
        },
      },
      {
        day_number: 8,
        date: 'Sat, Oct 25, 2025',
        city: 'Kanazawa',
        theme: 'Kenroku-en Gardens & Ancient Artisanal Chaya Guilds',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Kenroku-en Gardens Dawn Walk',
              category: 'NATURE',
              city: 'Kanazawa',
              estimated_cost_inr: 800,
              description: 'One of the Three Great Gardens of Japan in crisp autumn light with pine yukizuri preparations.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Gold Leaf Gilding Workshop in Higashi Chaya',
              category: 'ART_CULTURE',
              city: 'Kanazawa',
              estimated_cost_inr: 3200,
              description: 'Hands-on lacquerware gilding with master artisan custodian.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Omicho Market Coastal Sashimi Donburi',
            cuisine: 'Seafood',
            estimated_cost_inr: 2800,
            restaurant_name: 'Omicho Ichiba-kan',
          },
          {
            meal_type: 'DINNER',
            name: 'Coastal Seafood Feast & Local Ishikawa Sake',
            cuisine: 'Seafood & Sake',
            estimated_cost_inr: 4500,
            restaurant_name: 'Omicho Shokudo',
          },
        ],
        metrics: {
          active_hours: 5.5,
          rest_hours: 2.5,
          walking_steps: 8800,
          walking_km: 6.4,
          pacing_label: 'Artisanal Guild Discovery',
        },
        weather_forecast: {
          condition: 'Cool Coastal',
          temp_celsius: 14,
          temp_high_celsius: 16,
          temp_low_celsius: 7,
          precipitation_chance: 15,
          advisory: '15% coastal drizzle; indoor gold leaf studio scheduled for afternoon.',
        },
        stay: {
          name: 'Coastal Heritage Ryokan & Onsen',
          type: 'Artisanal Ryokan',
          neighborhood: 'Higashi Chaya',
          cost_inr: 12000,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 4000,
          meals_inr: 7300,
          transit_inr: 900,
          stays_inr: 12000,
          total_inr: 24200,
        },
        next_day_teaser: {
          day_number: 9,
          theme: 'Nagamachi Samurai District & 21st Century Contemporary Art',
          city: 'Kanazawa',
        },
      },
      {
        day_number: 9,
        date: 'Sun, Oct 26, 2025',
        city: 'Kanazawa',
        theme: 'Nagamachi Samurai District & 21st Century Contemporary Art',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Nagamachi Samurai District Mud Wall Stroll',
              category: 'HISTORY_HERITAGE',
              city: 'Kanazawa',
              estimated_cost_inr: 1100,
              description: 'Earthen walls, water canals, and Nomura Samurai Clan Residence garden.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: '21st Century Museum of Contemporary Art',
              category: 'ART_CULTURE',
              city: 'Kanazawa',
              estimated_cost_inr: 1800,
              description: 'Circular glass museum featuring Leandro Erlich’s Swimming Pool installation.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Kaga Jibu-ni Duck Stew Lunch',
            cuisine: 'Kaga Traditional Stew',
            estimated_cost_inr: 3200,
            restaurant_name: 'Kotobukiya',
          },
          {
            meal_type: 'DINNER',
            name: 'Farewell Hokuriku Kaiseki Dinner',
            cuisine: 'High-end Kaiseki',
            estimated_cost_inr: 6800,
            restaurant_name: 'Tsubaki',
          },
        ],
        metrics: {
          active_hours: 5.0,
          rest_hours: 3.0,
          walking_steps: 7600,
          walking_km: 5.4,
          pacing_label: 'Cultural Balance',
        },
        weather_forecast: {
          condition: 'Crisp Autumn',
          temp_celsius: 13,
          temp_high_celsius: 15,
          temp_low_celsius: 6,
          precipitation_chance: 5,
          advisory: 'Clear afternoon light for glass museum galleries.',
        },
        stay: {
          name: 'Coastal Heritage Ryokan & Onsen',
          type: 'Artisanal Ryokan',
          neighborhood: 'Higashi Chaya',
          cost_inr: 12000,
          confirmed: true,
        },
        day_budget: {
          activities_inr: 2900,
          meals_inr: 10000,
          transit_inr: 800,
          stays_inr: 12000,
          total_inr: 25700,
        },
        next_day_teaser: {
          day_number: 10,
          theme: 'Hokuriku Shinkansen High-Speed Return & Departure',
          city: 'Tokyo / Departure Gateway',
        },
      },
      {
        day_number: 10,
        date: 'Mon, Oct 27, 2025',
        city: 'Kanazawa / Departure Gateway',
        theme: 'Hokuriku Shinkansen High-Speed Return & Departure',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Morning Omicho Market Souvenir & Green Tea Selection',
              category: 'FOOD_EXPERIENCE',
              city: 'Kanazawa',
              estimated_cost_inr: 2000,
              description: 'Selecting premium Kaga bancha tea and gold leaf confectioneries.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Kagayaki Shinkansen High-Speed Bullet Transit to Tokyo Gateway',
              category: 'LOCAL_EXPERIENCE',
              city: 'Kanazawa to Tokyo',
              estimated_cost_inr: 7200,
              description: 'Effortless 2h 28m bullet train ride across the Japan Alps directly into international terminals.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'LUNCH',
            name: 'Artisanal Crab & Salmon Oshizushi Bento',
            cuisine: 'Pressed Sushi Bento',
            estimated_cost_inr: 2600,
            restaurant_name: 'Kanazawa Hyakubangai',
          },
        ],
        metrics: {
          active_hours: 3.5,
          rest_hours: 4.5,
          walking_steps: 5100,
          walking_km: 3.8,
          pacing_label: 'Unhurried Journey Conclusion',
        },
        weather_forecast: {
          condition: 'Clear Autumn',
          temp_celsius: 15,
          temp_high_celsius: 17,
          temp_low_celsius: 8,
          precipitation_chance: 0,
          advisory: 'Clear traveling skies across the Japan Alps.',
        },
        day_budget: {
          activities_inr: 9200,
          meals_inr: 2600,
          transit_inr: 600,
          stays_inr: 0,
          total_inr: 12400,
        },
      },
    ],
    total_activity_cost_inr: 52000,
    total_food_cost_inr: 46000,
    highlights: [
      {
        day: 3,
        city: 'Kyoto',
        title: 'Quiet Dawn Walk: Ninenzaka & Sannenzaka Slopes',
        description:
          'Ascent to Kiyomizu-dera via historic preservation alleyways before daytime tour groups, immersed in early morning monk bells.',
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCG57e8ef7Xyy2U_WOF_V6Yle3aoPJ4Asru2sAhk_c8zp5Sp-rdBstMJQDzC1j1Rccj5fLCeQ0TMIXiT4psUkBWNH9ex-Qcdv1wEY8K4yZN0X78a-LRasqcop7xe-sCVjGBQVF2dgbSJZ5rWRfCzHl9NLdmTmOjnLAXvAkTwDflPCadNBP6RmZpFB83bhEjeWCyRjJ8H6Bd1h5aeBkyQe7NvMdfP6KG6Jgb8LDMThs13buRLLnux0JK0A',
      },
      {
        day: 3,
        city: 'Kyoto',
        title: 'Private Dawn Tea at Nanzen-ji Sub-temple',
        description:
          'Uncrowded garden contemplation before general gates open. A 16th-generation tea master introduces morning matcha and seasonal wagashi.',
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBL9JOQUkAr1UHWHX0MKx5vbG_xYKSlkYW4AbC9tkGkMEogf-1sN3yLQHATN2KI0sXypCMh4lMQrgHiS5DhoCLtb7sQhbq3y3jv-FyxUnlEmVifZA8x_FdsORAsFA_YkVd_DpNHSsxoyIYRD1e1Odl6vIQ4BJ0DACx-IYgdW6CbgGhAIOSJeW9ABf6ZjmDBmG32_PWUUS04pg0TKyNJIHFDoggINhMHOFHoTvvGC10Q0SD-iGCNVCRmVw',
      },
      {
        day: 1,
        city: 'Osaka',
        title: 'Evening Dotonbori Secret Alleyway Tasting',
        description:
          'Handpicked takoyaki & seasonal dashi broths with a neighborhood chef. Avoid tourist lines through residential back-alleys.',
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuDYIhoNvkHAWligV8e5cXtEObIZzyZIFEDc90x349DWixd6W3pYOBUFfvnYwGWb3QDkjlkK_JJ5EzSKpyQOemvr8F-qhWAvhcSGJbDphQfcsi_FA6kk2N1Ka7LlcefASB6Yu6yoEi-oqPW5QLhsQ2AKukp4tcorle61RTMd_pkfDG-s2lsdgvR7ZPUqA39cVBIXm0E4infSMJDSDm_y-OW2eQ3XxUdzdtUGLCvGnuSedOxJ5szyCRH9TQ',
      },
      {
        day: 8,
        city: 'Kanazawa',
        title: 'Gold Leaf Gilding & Chaya Tea Guilds',
        description:
          'Hands-on lacquerware workshop in Higashi Chaya, accompanied by a local artisan custodian explaining four centuries of guild history.',
        image_url:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBN8A05kGXJJI6AmSXqUlBf3j1SAyGk10hS4t-FKrnzCkVF74fC_TJFz_kVHkqUQRYIy4fYTj7OrEnoAHExMw97n4bkxsJ7nmUDnfnf8Bm1SJFz-6YcuYICbZ1SlON4fQ1wxp8pxSnp8bocHaXWpyA2at_NDqH_nng9V3nbfnwAvGrnsr0hljDfC-UvzfeZRHZTh8_ZPtIeCydobYPUqXwIrIDFPXWGtldmJof5pyk-U69W_JzeiKy6rQ',
      },
    ],
  },
  budget_breakdown: {
    total_with_contingency_inr: 362400,
    subtotal_inr: 334800,
    contingency_inr: 27600,
    stays_inr: 142000,
    transport_inr: 94800,
    activities_inr: 52000,
    food_inr: 46000,
    contingency_percentage: 8,
    variance: {
      user_budget_inr: 380000,
      variance_inr: 17600,
      variance_percentage: 4.6,
      status: 'FAVORABLE',
    },
  },
  visa_verdict: {
    is_domestic_bypass: false,
    status: 'eVisa / Embassy Visa Required',
    notes: 'Single-entry tourist visa eligible with 15-day turnaround.',
  },
  weather_context: [
    {
      city: 'Osaka',
      temp: '18°C',
      condition: 'Sunny / Dry',
      icon: 'sunny',
      note: 'Light jacket recommended for evening canal walks',
    },
    {
      city: 'Kyoto',
      temp: '16°C',
      condition: 'Crisp Autumn',
      icon: 'park',
      note: 'Peak foliage hue index 92% across East Hills',
    },
    {
      city: 'Kanazawa',
      temp: '14°C',
      condition: 'Cool Coastal',
      icon: 'cloud',
      note: '15% drizzle (indoor atelier scheduled)',
    },
  ],
  plan_status: 'COMPLETED',
  created_at: new Date().toISOString(),
};

/**
 * Returns a DestinationDetail object for the given destination name,
 * either from curated records or dynamically synthesized from trip context.
 */
export const getDestinationDetail = (
  destinationName: string,
  itinerary: FinalItinerary
): DestinationDetail => {
  const normalized = destinationName.trim();
  const directMatch = Object.keys(SAMPLE_DESTINATION_DETAILS).find(
    (key) => key.toLowerCase() === normalized.toLowerCase()
  );

  if (directMatch) {
    const detail = { ...SAMPLE_DESTINATION_DETAILS[directMatch] };
    const idx = itinerary.trip_context.destinations.findIndex(
      (d) => d.toLowerCase() === normalized.toLowerCase()
    );
    if (idx !== -1) {
      detail.stop_number = idx + 1;
      detail.total_stops = itinerary.trip_context.destinations.length;
      const stay = itinerary.logistics_plan.hotel_stays[idx];
      if (stay) {
        detail.nights = stay.nights;
        detail.stay_dates = `${stay.check_in} – ${stay.check_out}`;
      }
    }
    return detail;
  }

  // Synthesize for any custom destination
  const stopIndex = Math.max(
    0,
    itinerary.trip_context.destinations.findIndex(
      (d) => d.toLowerCase() === normalized.toLowerCase()
    )
  );
  const totalStops = itinerary.trip_context.destinations.length || 1;
  const stay = itinerary.logistics_plan.hotel_stays[stopIndex];
  const nextDest = itinerary.trip_context.destinations[stopIndex + 1];

  return {
    name: destinationName,
    native_script: destinationName.slice(0, 2).toUpperCase(),
    region: 'Primary Cultural Hub',
    country: itinerary.trip_context.scope === 'DOMESTIC' ? 'India' : 'International',
    stop_number: stopIndex + 1,
    total_stops: totalStops,
    nights: stay?.nights || 2,
    stay_dates: stay ? `${stay.check_in} – ${stay.check_out}` : 'Curated Stay Window',
    hero_image:
      itinerary.cover_image?.url ||
      SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
    editorial_intro: `A focal center of your bespoke itinerary, selected for authentic cultural character, serene morning exploration paths, and regional heritage lodging.`,
    sanctuary_lodging_callout: `Anchored at ${stay?.hotel_name || 'Curated Heritage Stay'} in ${stay?.neighborhood || destinationName} with verified comfort amenities.`,
    snapshot: {
      recommended_stay: `${stay?.nights || 2}–${(stay?.nights || 2) + 1} Nights (Your Trip: ${stay?.nights || 2} Nights)`,
      seasonal_context: 'Optimal Local Season',
      weather_context: 'Pleasant & Moderate (Low Precipitation Risk)',
      currency_fx: itinerary.trip_context.scope === 'DOMESTIC' ? 'Indian Rupee (INR)' : 'Foreign Currency (~Market Rates)',
      language: itinerary.trip_context.scope === 'DOMESTIC' ? 'Hindi / Regional Language & English' : 'Local Language & English',
      timezone: itinerary.trip_context.scope === 'DOMESTIC' ? 'IST (UTC+5:30)' : 'Standard Local Timezone',
    },
    curator_selection: {
      quote: `Structured to offer an immersive sense of place while providing generous leisure buffers between morning excursions and evening dining.`,
      tags: ['Culture & Heritage', 'Local Cuisine', 'Mindful Pacing'],
      active_discovery_hours: 5.5,
      active_ratio_percent: 70,
      leisure_ratio_percent: 30,
    },
    neighborhoods: [
      {
        id: 'central-quarter',
        name: `${destinationName} Historic Core`,
        description: `Atmospheric lanes, landmark viewpoints, and authentic artisanal workshops.`,
        recommended_time: 'Morning (08:00 – 11:30)',
        duration: '3.0 Hours',
        highlights: ['Heritage Walking Trail', 'Local Market Discovery', 'Artisanal Workshops'],
        image_url:
          itinerary.cover_image?.url ||
          SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
      },
    ],
    mobility_guide: {
      arrival_overview: `Seamless arrival via coordinated inter-city transit corridor with luggage assistance.`,
      local_transit: `Local transit hubs and trusted verified vehicle services connect all key waypoints.`,
      walking_notes: `Comfortable walking paths throughout historic quarters; wear supportive walking footwear.`,
    },
    next_stop: nextDest
      ? {
          destination: nextDest,
          transport_mode: 'REGIONAL_TRANSIT',
          service_name: 'Scenic Coordinated Rail / Transit',
          duration: 'Direct Transfer',
          leg_id: `leg-${stopIndex + 2}`,
        }
      : undefined,
  };
};

/**
 * Returns a rich TransportLeg for the given leg ID, falling back to synthesis.
 */
export const getTransportLegDetail = (
  legId: string,
  itinerary: FinalItinerary
): TransportLeg => {
  const found = itinerary.logistics_plan.transport_legs.find((leg) => leg.id === legId);
  if (found && found.milestones && found.milestones.length > 0) {
    return found;
  }

  // If found without milestones or not found, enrich
  const baseLeg = found || itinerary.logistics_plan.transport_legs[0] || {
    id: 'leg-default',
    origin: itinerary.trip_context.origin,
    destination: itinerary.trip_context.destinations[0] || 'Destination',
    mode: 'TRAIN',
    duration: '2h 15m',
    cost_inr: 4500,
  };

  return {
    ...baseLeg,
    service_name: baseLeg.service_name || `${baseLeg.operator || 'Regional Express'} Transit Service`,
    carrier: baseLeg.carrier || 'Coordinated Regional Transit',
    equipment: baseLeg.equipment || 'High-Comfort Air-Conditioned Coach',
    seat_reservation: baseLeg.seat_reservation || 'Reserved Premium Forward Window Seats',
    travel_date: baseLeg.travel_date || itinerary.trip_context.start_date,
    distance_km: baseLeg.distance_km || 185.5,
    luggage_policy:
      baseLeg.luggage_policy ||
      'Luggage porter assistance and dedicated luggage racks in reserved carriages.',
    pass_coverage: baseLeg.pass_coverage || 'Included in Curated Transit Package',
    fare_breakdown: baseLeg.fare_breakdown || {
      base_fare_inr: Math.round(baseLeg.cost_inr * 0.65),
      seat_reservation_inr: Math.round(baseLeg.cost_inr * 0.35),
      currency_local: 'INR',
      total_local: `₹${baseLeg.cost_inr.toLocaleString('en-IN')}`,
      status: 'Confirmed & Included in Package',
    },
    milestones: baseLeg.milestones || [
      {
        time: '09:00',
        label: 'Sanctuary Departure',
        location: baseLeg.origin,
        description: `Check-out and transfer to terminal with coordinated luggage clearance.`,
        icon: 'hotel',
        status: 'completed',
      },
      {
        time: '09:45',
        label: 'Terminal Check-in',
        location: `${baseLeg.origin} Station / Terminal`,
        description: `Security and trackside arrival with light breakfast refreshment buffer.`,
        icon: 'train',
        status: 'completed',
      },
      {
        time: '10:15 ➔ 12:30',
        label: 'Active Transit Segment',
        location: `Scenic Corridor`,
        description: `Unhurried transit offering picturesque landscape views from reserved panoramic seats.`,
        icon: 'directions_railway',
        status: 'active',
      },
      {
        time: '12:30',
        label: 'Terminus Arrival',
        location: `${baseLeg.destination} Terminal`,
        description: `Arrival at central terminal with direct ground transit assistance.`,
        icon: 'location_on',
        status: 'upcoming',
      },
      {
        time: '13:00',
        label: 'Sanctuary Check-in',
        location: `${baseLeg.destination} Heritage Stay`,
        description: `Arrival at sanctuary hotel; baggage verified and orientation refreshment served.`,
        icon: 'spa',
        status: 'upcoming',
      },
    ],
    intermediate_stops: baseLeg.intermediate_stops || [
      { station: `${baseLeg.origin} Terminal`, time: '10:15 Dep', platform: 'Platform 1', notes: 'Origin' },
      { station: 'Scenic Mountain Valley Pass', time: '11:15', notes: 'Panoramic viewpoint' },
      { station: 'Regional Junction Point', time: '11:55', notes: 'Brief scheduled stop' },
      { station: `${baseLeg.destination} Station`, time: '12:30 Arr', platform: 'Platform 2', notes: 'Terminus' },
    ],
  };
};

/**
 * Dynamically synthesizes a FinalItinerary preview from any user's draft state.
 */
export const synthesizeItineraryFromDraft = (
  tripDetails: any,
  destinations: any[],
  preferences: any,
  budget: any
): FinalItinerary => {
  const isDomestic = tripDetails.scope === 'DOMESTIC';
  const duration = tripDetails.durationDays || 7;
  const userBudget = budget.budgetInr || (isDomestic ? 45000 : 180000);
  const adults = tripDetails.adults || 2;
  const travelersLabel = adults === 1 ? 'Solo Explorer' : `${adults} Explorers (${tripDetails.partyType || 'Couple'})`;

  const stops = destinations.length > 0 ? destinations : [{ name: tripDetails.destination, nights: duration }];
  const stopNames = stops.map((s) => s.name);

  const staysCost = Math.round(userBudget * 0.39);
  const transportCost = Math.round(userBudget * 0.26);
  const activitiesCost = Math.round(userBudget * 0.14);
  const foodCost = Math.round(userBudget * 0.13);
  const contingencyCost = Math.round(userBudget * 0.08);
  const totalEstimated = staysCost + transportCost + activitiesCost + foodCost + contingencyCost;
  const varianceInr = userBudget - totalEstimated;

  const primaryDest = stopNames[0] || 'Selected Destination';

  // Build daily plans for duration
  const days: DayPlan[] = Array.from({ length: duration }).map((_, idx) => {
    const dayNum = idx + 1;
    // Determine which stop this day falls into
    const stopIndex = Math.min(Math.floor((idx / duration) * stops.length), stops.length - 1);
    const currentStop = stops[stopIndex] || { name: primaryDest };
    const cityName = currentStop.name;

    return {
      day_number: dayNum,
      date: `Day ${dayNum}`,
      city: cityName,
      theme: `Cultural Immersion & Historic Landmarks in ${cityName}`,
      activities: [
        {
          daypart: 'MORNING',
          poi: {
            name: `Morning walking trail & architectural landmark visit in ${cityName}`,
            category: 'HISTORY_HERITAGE',
            city: cityName,
            estimated_cost_inr: 1200,
            description: 'Authentic early access stroll before crowds.',
            is_must_visit: dayNum === 1 || dayNum === 3,
          },
          notes: 'Optimal morning lighting; tranquil stroll through heritage lanes.',
        },
        {
          daypart: 'AFTERNOON',
          poi: {
            name: `Artisanal craft atelier & tea pause in ${cityName}`,
            category: 'LOCAL_EXPERIENCE',
            city: cityName,
            estimated_cost_inr: 1800,
            description: 'Immersion with local creators and guild custodians.',
          },
          notes: 'Hands-on interactive demonstration reserved.',
        },
        {
          daypart: 'EVENING',
          poi: {
            name: `Atmospheric twilight promenade along historic promenade in ${cityName}`,
            category: 'LOCAL_EXPERIENCE',
            city: cityName,
            estimated_cost_inr: 900,
            description: 'Unhurried dusk walk soaking in evening illumination and local life.',
          },
        },
      ],
      meals: [
        {
          meal_type: 'LUNCH',
          name: `Handcrafted Regional Specialties Lunch in ${cityName}`,
          cuisine: 'Authentic Regional Dining',
          estimated_cost_inr: 2200,
          restaurant_name: `${cityName} Heritage Dining Room`,
        },
        {
          meal_type: 'DINNER',
          name: `Regional specialties at trusted family restaurant in ${cityName}`,
          cuisine: 'Regional authentic dining',
          estimated_cost_inr: 3200,
          restaurant_name: `${cityName} Hearth & Grill`,
        },
      ],
      metrics: {
        active_hours: 5.0,
        rest_hours: 3.0,
        walking_steps: 7800,
        walking_km: 5.6,
        pacing_label: 'Balanced Discovery Cadence',
      },
      weather_forecast: {
        condition: 'Clear & Favorable',
        temp_celsius: 20,
        temp_high_celsius: 22,
        temp_low_celsius: 14,
        precipitation_chance: 0,
        advisory: 'Optimal temperatures for outdoor walking; carry light outerwear for evening.',
        icon: 'sunny',
      },
      stay: {
        name: `Boutique Heritage Haven — ${cityName}`,
        type: 'Curated Heritage Stay',
        neighborhood: currentStop.region || cityName,
        cost_inr: Math.round(staysCost / duration),
        confirmed: true,
        check_in: '15:00',
        amenities: ['Artisanal Breakfast', 'Private Courtyard', 'Dedicated Concierge', 'Luggage Forwarding'],
      },
      featured_experience: {
        title: `Morning Architectural Trail & Landmark Stroll in ${cityName}`,
        subtitle: `Unhurried early access to iconic heritage quarters before midday crowds.`,
        time_window: '08:00 – 10:30 (2h 30m Gentle Stroll)',
        duration: '2h 30m',
        image_url:
          currentStop.imageUrl ||
          SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
        tags: ['Pristine Light Window', 'Curator Highlight', 'Confirmed Entry'],
        why_included: `Selected as the experiential anchor for Day ${dayNum} to provide deep cultural context in ${cityName} without crowded tourist queues.`,
        curator_tips: [
          'Arrive early for soft morning illumination and undisturbed photography.',
          'Wear comfortable slip-on walking shoes suitable for historic stone alleys.',
          'Savor quiet contemplative moments in the inner courtyard before departure.',
        ],
        transit_connection: `10 min walk or private transfer from your boutique stay`,
      },
      hourly_atmosphere: [
        { time: '08:00', temp: '16°C', condition: 'Morning Crisp', precipitation: '0%', icon: 'wb_twilight' },
        { time: '11:00', temp: '20°C', condition: 'Mild Sun', precipitation: '0%', icon: 'sunny' },
        { time: '14:00', temp: '22°C', condition: 'Warm Afternoon', precipitation: '0%', icon: 'sunny' },
        { time: '17:00', temp: '19°C', condition: 'Golden Dusk', precipitation: '0%', icon: 'light_mode' },
        { time: '20:00', temp: '16°C', condition: 'Pleasant Night', precipitation: '0%', icon: 'bedtime' },
      ],
      day_budget: {
        activities_inr: 3900,
        meals_inr: 5400,
        transit_inr: 1000,
        stays_inr: Math.round(staysCost / duration),
        total_inr: 3900 + 5400 + 1000 + Math.round(staysCost / duration),
      },
      next_day_teaser:
        dayNum < duration
          ? {
              day_number: dayNum + 1,
              theme: `Exploration & Artisanal Discovery in ${stops[Math.min(Math.floor((idx + 1) / duration) * stops.length, stops.length - 1)]?.name || cityName}`,
              city: stops[Math.min(Math.floor((idx + 1) / duration) * stops.length, stops.length - 1)]?.name || cityName,
            }
          : undefined,
    };
  });

  return {
    trip_id: `SF-${Math.floor(1000 + Math.random() * 9000)}`,
    title: `${duration}-Day Journey through ${primaryDest}`,
    summary: `A carefully paced expedition across ${stopNames.join(', ')} tailored for ${travelersLabel} with an emphasis on authentic local character and mindful transit.`,
    curator_note: `Structured with generous leisure buffers to balance active discovery with restorative pauses. Inter-hub transfers feature optimized scenic routes and verified local lodging.`,
    cover_image: {
      url: stops[0]?.imageUrl || SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
      alt: stops[0]?.name || 'Journey cover',
      waypoint_title: `${primaryDest} at golden hour`,
      stay_highlight: `Curated Heritage Stay in central ${primaryDest}`,
      seasonal_badge: isDomestic ? 'Optimal Subcontinent Seasonal Window' : 'Favorable Global Transit Season',
    },
    pace_rhythm_index: {
      cultural_immersiveness: 92,
      transit_leisure_margin: 85,
      vetted_by: 'Senior Destination Architect',
    },
    trip_context: {
      origin: tripDetails.origin || 'New Delhi',
      destinations: stopNames,
      start_date: tripDetails.departureDate || 'Oct 18, 2025',
      end_date: tripDetails.returnDate || 'Oct 28, 2025',
      duration_days: duration,
      budget_inr: userBudget,
      num_travelers: adults,
      travel_style: preferences.travelStyle || 'COMFORTABLE',
      pace: preferences.pace || 'BALANCED',
      scope: tripDetails.scope || 'INTERNATIONAL',
    },
    logistics_plan: {
      transport_legs: stops.map((stop, idx) => ({
        id: `leg-${idx + 1}`,
        origin: idx === 0 ? (tripDetails.origin || 'New Delhi') : stops[idx - 1].name,
        destination: stop.name,
        mode: idx === 0 ? (isDomestic ? 'RAIL / FLIGHT' : 'INTERNATIONAL FLIGHT') : 'REGIONAL TRANSIT',
        service_name: idx === 0 ? 'Primary Gateway Transit' : `Express Corridor ${stop.name}`,
        operator: idx === 0 ? 'International Carrier' : 'Scenic Regional Express',
        carrier: idx === 0 ? 'National Carrier' : 'Regional Express Line',
        equipment: 'Comfort Air-Conditioned Coach',
        seat_reservation: 'Car 01 / Reserved Seating',
        duration: idx === 0 ? 'Direct Transit' : '2h 10m Scenic Route',
        travel_date: tripDetails.departureDate || 'Oct 18, 2025',
        distance_km: idx === 0 ? 1200 : 210,
        cost_inr: Math.round(transportCost / stops.length),
        notes: stop.transitToNext?.title || 'Comfortable coordinated leg',
        fare_breakdown: {
          base_fare_inr: Math.round((transportCost / stops.length) * 0.7),
          seat_reservation_inr: Math.round((transportCost / stops.length) * 0.3),
          currency_local: 'INR',
          total_local: `₹${Math.round(transportCost / stops.length).toLocaleString('en-IN')}`,
          status: 'Included in Curated Pass Package',
        },
        milestones: [
          {
            time: '09:00',
            label: 'Sanctuary Departure',
            location: idx === 0 ? tripDetails.origin || 'Origin' : stops[idx - 1].name,
            description: 'Departure and terminal check-in with dedicated luggage assistance.',
            icon: 'hotel',
            status: 'completed',
          },
          {
            time: '09:45',
            label: 'Boarding & Clearance',
            location: 'Main Terminal',
            description: 'Priority boarding and refreshment clearance.',
            icon: 'train',
            status: 'completed',
          },
          {
            time: '10:15 ➔ 12:30',
            label: 'Scenic Transit Segment',
            location: 'Scenic Route Corridor',
            description: `Comfortable journey toward ${stop.name} with panoramic scenic vistas.`,
            icon: 'directions_railway',
            status: 'active',
          },
          {
            time: '12:30',
            label: 'Terminus Arrival',
            location: `${stop.name} Station`,
            description: 'Arrival at destination terminal; ground transit met by local concierge.',
            icon: 'location_on',
            status: 'upcoming',
          },
          {
            time: '13:00',
            label: 'Sanctuary Check-in',
            location: `Boutique Haven ${stop.name}`,
            description: 'Luggage safely delivered and welcome refreshment served.',
            icon: 'spa',
            status: 'upcoming',
          },
        ],
        intermediate_stops: [
          { station: `${idx === 0 ? tripDetails.origin || 'Origin' : stops[idx - 1].name} Terminal`, time: '10:15 Dep' },
          { station: 'Scenic Intermediate Hub', time: '11:20' },
          { station: `${stop.name} Central Station`, time: '12:30 Arr' },
        ],
      })),
      hotel_stays: stops.map((stop, idx) => ({
        id: `stay-${idx + 1}`,
        hotel_name: `Boutique Heritage Haven — ${stop.name}`,
        city: stop.name,
        check_in: tripDetails.departureDate || 'Oct 18, 2025',
        check_out: tripDetails.returnDate || 'Oct 28, 2025',
        nights: stop.nights || 2,
        cost_inr: Math.round(staysCost / stops.length),
        neighborhood: stop.region || stop.name,
        style: 'Handcrafted Heritage Stay',
        confirmed: true,
      })),
      total_transport_cost_inr: transportCost,
      total_accommodation_cost_inr: staysCost,
    },
    experience_plan: {
      total_days: duration,
      days,
      total_activity_cost_inr: activitiesCost,
      total_food_cost_inr: foodCost,
      highlights: stops.slice(0, 3).map((stop, idx) => ({
        day: idx * 2 + 1,
        city: stop.name,
        title: `Curated Discovery Moment in ${stop.name}`,
        description: `Handcrafted immersion in the historic quarters of ${stop.name} avoiding crowded commercial routes.`,
        image_url: stop.imageUrl || SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
      })),
    },
    budget_breakdown: {
      total_with_contingency_inr: totalEstimated,
      subtotal_inr: totalEstimated - contingencyCost,
      contingency_inr: contingencyCost,
      stays_inr: staysCost,
      transport_inr: transportCost,
      activities_inr: activitiesCost,
      food_inr: foodCost,
      contingency_percentage: 8,
      variance: {
        user_budget_inr: userBudget,
        variance_inr: Math.abs(varianceInr),
        variance_percentage: Math.round((Math.abs(varianceInr) / userBudget) * 100 * 10) / 10,
        status: varianceInr >= 0 ? 'FAVORABLE' : 'UNFAVORABLE',
      },
    },
    visa_verdict: isDomestic
      ? { is_domestic_bypass: true, status: 'DOMESTIC_BYPASS', notes: 'No visa required within India' }
      : { is_domestic_bypass: false, status: 'Tourist Visa Guidance Available', notes: 'Check passport validity of 6+ months' },
    weather_context: stops.map((stop) => ({
      city: stop.name,
      temp: '20°C',
      condition: 'Pleasant & Clear',
      icon: 'sunny',
      note: 'Optimal walking climate with gentle morning breezes',
    })),
    plan_status: 'COMPLETED',
    created_at: new Date().toISOString(),
  };
};
