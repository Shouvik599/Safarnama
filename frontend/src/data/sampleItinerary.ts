import type { FinalItinerary } from '../types/itinerary';

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
        duration: '7h 45m',
        cost_inr: 45000,
        notes: 'Overnight transit · direct terminal clearance',
      },
      {
        id: 'leg-2',
        origin: 'Osaka (Umeda / Shin-Osaka)',
        destination: 'Kyoto Station',
        mode: 'SHINKANSEN',
        operator: 'Tokaido Shinkansen',
        duration: '15 min bullet rail',
        cost_inr: 2800,
        notes: 'Frequent departures every 10 mins',
      },
      {
        id: 'leg-3',
        origin: 'Kyoto Station',
        destination: 'Kanazawa Station',
        mode: 'TRAIN',
        operator: 'JR Thunderbird Express / Shinkansen',
        duration: '2h 10m scenic lakeside',
        cost_inr: 6500,
        notes: 'Scenic Lake Biwa route with forward luggage dispatch',
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
        date: 'Oct 18, 2025',
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
      },
      {
        day_number: 4,
        date: 'Oct 21, 2025',
        city: 'Kyoto',
        theme: 'Dawn Contemplation & Higashiyama Temples',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Private Dawn Tea at Nanzen-ji Sub-temple',
              category: 'SPIRITUAL',
              city: 'Kyoto',
              estimated_cost_inr: 4500,
              description: 'Uncrowded garden contemplation before general gates open with 16th-generation tea master.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Kiyomizu-dera & Otowa Sacred Falls',
              category: 'HISTORY_HERITAGE',
              city: 'Kyoto',
              estimated_cost_inr: 1800,
              description: 'Ancient wooden stage overlooking peak momiji maple foliage.',
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
          },
        ],
      },
      {
        day_number: 8,
        date: 'Oct 25, 2025',
        city: 'Kanazawa',
        theme: 'Kenroku-en & Ancient Artisanal Chaya Guilds',
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: 'Kenroku-en Gardens Dawn Walk',
              category: 'NATURE',
              city: 'Kanazawa',
              estimated_cost_inr: 800,
              description: 'One of the Three Great Gardens of Japan in crisp autumn light.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: 'Gold Leaf Gilding Workshop in Higashi Chaya',
              category: 'ART_CULTURE',
              city: 'Kanazawa',
              estimated_cost_inr: 3200,
              description: 'Hands-on lacquerware gilding with master craftsman.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'DINNER',
            name: 'Omicho Market Coastal Seafood Feast',
            cuisine: 'Seafood & Sake',
            estimated_cost_inr: 4500,
            restaurant_name: 'Omicho Shokudo',
          },
        ],
      },
    ],
    total_activity_cost_inr: 52000,
    total_food_cost_inr: 46000,
    highlights: [
      {
        day: 4,
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
      start_date: tripDetails.departureDate || 'Selected Date',
      end_date: tripDetails.returnDate || 'Return Date',
      duration_days: duration,
      budget_inr: userBudget,
      num_travelers: adults,
      travel_style: preferences.travelStyle || 'COMFORTABLE',
      pace: preferences.pace || 'BALANCED',
      scope: tripDetails.scope || 'INTERNATIONAL',
    },
    logistics_plan: {
      transport_legs: stops.map((stop, idx) => ({
        id: `leg-${idx}`,
        origin: idx === 0 ? tripDetails.origin : stops[idx - 1].name,
        destination: stop.name,
        mode: idx === 0 ? (isDomestic ? 'RAIL / FLIGHT' : 'INTERNATIONAL FLIGHT') : 'REGIONAL TRANSIT',
        duration: idx === 0 ? 'Direct Transit' : 'Scenic Route',
        cost_inr: Math.round(transportCost / stops.length),
        notes: stop.transitToNext?.title || 'Comfortable coordinated leg',
      })),
      hotel_stays: stops.map((stop, idx) => ({
        id: `stay-${idx}`,
        hotel_name: `Boutique Heritage Haven — ${stop.name}`,
        city: stop.name,
        check_in: tripDetails.departureDate,
        check_out: tripDetails.returnDate,
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
      days: stops.map((stop, idx) => ({
        day_number: idx + 1,
        date: `Day ${idx + 1}`,
        city: stop.name,
        theme: `Exploring the heritage & cultural character of ${stop.name}`,
        activities: [
          {
            daypart: 'MORNING',
            poi: {
              name: `Morning walking trail & landmark visit in ${stop.name}`,
              category: 'HISTORY_HERITAGE',
              city: stop.name,
              estimated_cost_inr: 1200,
              description: 'Authentic early access stroll before crowds.',
            },
          },
          {
            daypart: 'AFTERNOON',
            poi: {
              name: `Artisanal craft atelier & tea pause in ${stop.name}`,
              category: 'LOCAL_EXPERIENCE',
              city: stop.name,
              estimated_cost_inr: 1800,
              description: 'Immersion with local creators.',
            },
          },
        ],
        meals: [
          {
            meal_type: 'DINNER',
            name: `Regional specialties at trusted family restaurant in ${stop.name}`,
            cuisine: 'Regional authentic dining',
            estimated_cost_inr: 2400,
          },
        ],
      })),
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
