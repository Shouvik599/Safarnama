import type { RouteStop, DestinationSuggestion, ContextualCityItem } from '../types/trip';
import {
  PRECONFIGURED_CIRCUITS,
  INDIAN_ORIGIN_AIRPORTS,
  getDomesticPermitStatus,
  getMultiDestinationVisaVerdict,
} from './locations';
import generatedCountries from './generated_countries.json';
import indianStatesUts from './indian_states_uts.json';
import indiaPlacesData from './india_places.json';

export interface DestinationItem {
  id: string;
  name: string;
  alias: string;
  scope: 'DOMESTIC' | 'INTERNATIONAL';
  type: 'STATE' | 'UT' | 'COUNTRY' | 'CIRCUIT';
  visaStatus: string;
  defaultDurationDays: number;
  seasonSummary: string;
  defaultStops: RouteStop[];
  suggestions: DestinationSuggestion[];
}

// -------------------------------------------------------------
// 1. CURATED DOMESTIC CIRCUITS, STATES & UNION TERRITORIES
// -------------------------------------------------------------
export const DOMESTIC_DESTINATIONS: DestinationItem[] = [
  {
    id: 'rajasthan',
    name: 'Rajasthan (Jaipur, Jodhpur, Udaipur & Jaisalmer)',
    alias: 'Rajasthan Royals',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: '',
    defaultDurationDays: 10,
    seasonSummary: 'Optimal Season: Mild Winter Sunshine & Desert Festivals',
    defaultStops: [
      {
        id: 'jaipur',
        name: 'Jaipur',
        country: 'India',
        nights: 3,
        role: 'Pink City Forts',
        imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Amber Fort in Jaipur Rajasthan overlooking Maota Lake',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~4 hrs transit',
          title: 'Express Intercity Train to Jodhpur',
        },
      },
      {
        id: 'jodhpur',
        name: 'Jodhpur',
        country: 'India',
        nights: 2,
        role: 'Blue City & Mehrangarh',
        imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Mehrangarh Fort towering above blue houses of Jodhpur',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~4 hrs 30 mins',
          title: 'Private Chauffeur via Ranakpur Jain Temples',
        },
      },
      {
        id: 'udaipur',
        name: 'Udaipur',
        country: 'India',
        nights: 3,
        role: 'City of Lakes & Palaces',
        imageUrl: 'https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Lake Pichola in Udaipur with historic City Palace reflection',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~5 hrs transit',
          title: 'Desert Express Train to Jaisalmer',
        },
      },
      {
        id: 'jaisalmer',
        name: 'Jaisalmer',
        country: 'India',
        nights: 2,
        role: 'Golden Fort & Thar Desert',
        imageUrl: 'https://images.unsplash.com/photo-1600100397608-f010e42f9b20?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Golden sandstone ramparts of Jaisalmer fort in Thar desert',
      },
    ],
    suggestions: [
      {
        id: 'ranthambore',
        name: 'Ranthambore National Park',
        region: 'Sawai Madhopur, Rajasthan',
        tag: 'Bengal Tiger Safari',
        description: 'Historic jungle reserve renowned for royal Bengal tiger encounters around ancient ruins.',
        imageUrl: 'https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'pushkar',
        name: 'Pushkar & Brahma Lake',
        region: 'Ajmer, Rajasthan',
        tag: 'Sacred Lake & Desert Ghats',
        description: 'Vibrant pilgrim town with sacred ghats, rose gardens, and desert sand dunes.',
        imageUrl: 'https://images.unsplash.com/photo-1548013146-72479768bada?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'himachal',
    name: 'Himachal Pradesh (Shimla, Manali & Dharamshala)',
    alias: 'Himachal Hills',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: '',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Snow-Capped Peaks & Fresh Mountain Pines',
    defaultStops: [
      {
        id: 'shimla',
        name: 'Shimla',
        country: 'India',
        nights: 3,
        role: 'Colonial Hill Capital',
        imageUrl: 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Shimla Mall Road ridge framed by cedar pines and Himalayan peaks',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~6 hrs transit',
          title: 'Scenic Mountain Highway via Kullu Valley',
        },
      },
      {
        id: 'manali',
        name: 'Manali & Solang Valley',
        country: 'India',
        nights: 3,
        role: 'Alpine Passes & Snow Valley',
        imageUrl: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Snow covered Himalayan mountains around Solang Valley Manali',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~6 hrs transit',
          title: 'Mountain Pass Drive to Kangra Valley',
        },
      },
      {
        id: 'dharamshala',
        name: 'Dharamshala & McLeod Ganj',
        country: 'India',
        nights: 2,
        role: 'Little Lhasa & Monasteries',
        imageUrl: 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Prayer flags overlooking Dhauladhar mountain range in McLeod Ganj',
      },
    ],
    suggestions: [
      {
        id: 'kasol',
        name: 'Kasol & Parvati Valley',
        region: 'Kullu, Himachal Pradesh',
        tag: 'Pine Trails & Riverbanks',
        description: 'Tranquil riverside sanctuary known for pine forests and alpine hikes to Tosh and Kheerganga.',
        imageUrl: 'https://images.unsplash.com/photo-1596761611016-186165ed2e00?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'bir',
        name: 'Bir Billing',
        region: 'Kangra, Himachal Pradesh',
        tag: 'Paragliding Capital',
        description: 'World-renowned takeoff site for paragliding over tea estates and Tibetan monasteries.',
        imageUrl: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'goa',
    name: 'Goa (North Beaches, Panaji Heritage & South Serenity)',
    alias: 'Goa Stays',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: '',
    defaultDurationDays: 6,
    seasonSummary: 'Optimal Season: Sunny Coastal Breezes & Vibrant Beach Life',
    defaultStops: [
      {
        id: 'north-goa',
        name: 'North Goa (Anjuna & Vagator)',
        country: 'India',
        nights: 3,
        role: 'Coastlines & Sunsets',
        imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Palm fringed beach cove in North Goa at sunset',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~1 hr 15 mins',
          title: 'Coastal Drive via Panaji Latin Quarter',
        },
      },
      {
        id: 'south-goa',
        name: 'South Goa (Palolem & Benaulim)',
        country: 'India',
        nights: 3,
        role: 'White Sands & Serenity',
        imageUrl: 'https://images.unsplash.com/photo-1587922546307-776227941871?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Quiet crescent bay of Palolem Beach in South Goa',
      },
    ],
    suggestions: [
      {
        id: 'dudhsagar',
        name: 'Dudhsagar Waterfalls',
        region: 'Mollem National Park, Goa',
        tag: 'Four-Tiered Jungle Cascade',
        description: 'Spectacular jungle cataract cascading 310 meters down the Western Ghats.',
        imageUrl: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
      {
        id: 'old-goa',
        name: 'Old Goa & Fontainhas',
        region: 'Panaji, Goa',
        tag: 'Portuguese Heritage',
        description: 'UNESCO basilica and colorful 18th-century Portuguese villas with terracotta roofs.',
        imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'kashmir',
    name: 'Jammu & Kashmir (Srinagar, Gulmarg & Pahalgam)',
    alias: 'Kashmir Valley',
    scope: 'DOMESTIC',
    type: 'UT',
    visaStatus: '',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Emerald Valleys, Shikara Cruises & Snow Meadows',
    defaultStops: [
      {
        id: 'srinagar',
        name: 'Srinagar',
        country: 'India',
        nights: 3,
        role: 'Dal Lake & Mughal Gardens',
        imageUrl: 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Traditional wooden Shikara boat drifting on serene Dal Lake Srinagar',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~2 hrs transit',
          title: 'Scenic Meadow Drive to Gulmarg',
        },
      },
      {
        id: 'gulmarg',
        name: 'Gulmarg',
        country: 'India',
        nights: 2,
        role: 'High Meadows & Gondola',
        imageUrl: 'https://images.unsplash.com/photo-1624806992066-5ffcf7ca186b?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Gulmarg meadow surrounded by snow-capped Pir Panjal peaks',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~3 hrs 30 mins',
          title: 'River Road Transfer to Pahalgam',
        },
      },
      {
        id: 'pahalgam',
        name: 'Pahalgam',
        country: 'India',
        nights: 3,
        role: 'Lidder River & Betaab Valley',
        imageUrl: 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Pristine Lidder river flowing through pine valley of Pahalgam',
      },
    ],
    suggestions: [
      {
        id: 'sonamarg',
        name: 'Sonamarg & Thajiwas Glacier',
        region: 'Ganderbal, Kashmir',
        tag: 'Meadow of Gold',
        description: 'Gateway to Ladakh featuring turquoise glacier melt streams and high mountain meadows.',
        imageUrl: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  },
  {
    id: 'uttarakhand',
    name: 'Uttarakhand (Rishikesh, Mussoorie & Nainital)',
    alias: 'Devbhoomi Hills',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: '',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Crisp Alpine Air, Ganga Ghats & Lake Vistas',
    defaultStops: [
      {
        id: 'rishikesh',
        name: 'Rishikesh',
        country: 'India',
        nights: 3,
        role: 'Ganga Valley & Yoga Capital',
        imageUrl: 'https://images.unsplash.com/photo-1600100397608-f010e42f9b20?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Laxman Jhula suspension bridge over holy Ganges in Rishikesh',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~2 hrs 30 mins',
          title: 'Hill Highway to Mussoorie',
        },
      },
      {
        id: 'mussoorie',
        name: 'Mussoorie',
        country: 'India',
        nights: 2,
        role: 'Queen of Hills & Doon Valley',
        imageUrl: 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Mussoorie ridge overlooking misty Doon valley at sunset',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~6 hrs transit',
          title: 'Kumaon Foothills Highway to Nainital',
        },
      },
      {
        id: 'nainital',
        name: 'Nainital',
        country: 'India',
        nights: 3,
        role: 'Lake District & Kumaon',
        imageUrl: 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Emerald waters of Naini Lake surrounded by forested hills',
      },
    ],
    suggestions: [
      {
        id: 'corbett',
        name: 'Jim Corbett National Park',
        region: 'Nainital District, Uttarakhand',
        tag: 'Oldest Tiger Reserve',
        description: 'Dense sal forest sanctuaries famed for wild elephants, leopards, and Bengal tigers.',
        imageUrl: 'https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  },
  {
    id: 'andaman',
    name: 'Andaman & Nicobar (Port Blair, Havelock & Neil Island)',
    alias: 'Andaman Islands',
    scope: 'DOMESTIC',
    type: 'UT',
    visaStatus: '',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Turquoise Tropical Waters & Coral Snorkeling',
    defaultStops: [
      {
        id: 'port-blair',
        name: 'Port Blair',
        country: 'India',
        nights: 2,
        role: 'Island Gateway & History',
        imageUrl: 'https://images.unsplash.com/photo-1587922546307-776227941871?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Historic cellular jail and turquoise coastline of Port Blair',
        transitToNext: {
          mode: 'ferry',
          icon: 'directions_boat',
          duration: '~1 hr 30 mins',
          title: 'Makruzz High-Speed Island Catamaran',
        },
      },
      {
        id: 'havelock',
        name: 'Havelock Island (Swaraj Dweep)',
        country: 'India',
        nights: 4,
        role: 'Radhanagar White Sands',
        imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Radhanagar Beach on Havelock Island with azure waters and white sand',
        transitToNext: {
          mode: 'ferry',
          icon: 'directions_boat',
          duration: '~1 hr transit',
          title: 'Inter-Island Catamaran to Neil',
        },
      },
      {
        id: 'neil',
        name: 'Neil Island (Shaheed Dweep)',
        country: 'India',
        nights: 2,
        role: 'Natural Rock Bridge & Corals',
        imageUrl: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Natural limestone bridge formed by sea waves on Neil Island',
      },
    ],
    suggestions: [
      {
        id: 'elephant-beach',
        name: 'Elephant Beach Reef',
        region: 'Havelock Island, Andaman',
        tag: 'Sea Walking & Sea Turtles',
        description: 'Vibrant coral reef accessible by forest trail or speedboat with crystal visibility.',
        imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'sikkim',
    name: 'Sikkim & Darjeeling (Gangtok, Pelling & Darjeeling)',
    alias: 'Sikkim Peaks',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: 'ℹ️ Inner Line Permit (ILP) / PAP Required',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Kanchenjunga Panoramas & Buddhist Monasteries',
    defaultStops: [
      {
        id: 'gangtok',
        name: 'Gangtok',
        country: 'India',
        nights: 3,
        role: 'Himalayan Ridge Capital',
        imageUrl: 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Gangtok city overlooking misty Himalayan ridges and Rumtek Monastery',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~4 hrs 30 mins',
          title: 'Scenic Mountain Drive to Pelling',
        },
      },
      {
        id: 'pelling',
        name: 'Pelling',
        country: 'India',
        nights: 2,
        role: 'Kanchenjunga Sanctuary',
        imageUrl: 'https://images.unsplash.com/photo-1624806992066-5ffcf7ca186b?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Golden morning sunrise hitting Kanchenjunga peak from Pelling',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~3 hrs 30 mins',
          title: 'Tea Estate Mountain Road to Darjeeling',
        },
      },
      {
        id: 'darjeeling',
        name: 'Darjeeling',
        country: 'India',
        nights: 3,
        role: 'Queen of the Hills & Tea Gardens',
        imageUrl: 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Verdant rolling tea plantations in Darjeeling under blue skies',
      },
    ],
    suggestions: [
      {
        id: 'tsomgo',
        name: 'Tsomgo Lake & Nathula Pass',
        region: 'East Sikkim',
        tag: 'Glacial Alpine Lake (12,400ft)',
        description: 'Sacred high-altitude lake surrounded by rugged mountains on the historic Silk Route.',
        imageUrl: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'karnataka',
    name: 'Karnataka (Bengaluru, Mysuru, Coorg & Hampi)',
    alias: 'Karnataka Heritage',
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: '',
    defaultDurationDays: 9,
    seasonSummary: 'Optimal Season: Pleasant Deccan Weather & Coffee Harvest',
    defaultStops: [
      {
        id: 'bengaluru',
        name: 'Bengaluru',
        country: 'India',
        nights: 2,
        role: 'Silicon Garden City',
        imageUrl: 'https://images.unsplash.com/photo-1596761611016-186165ed2e00?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Bengaluru cityscape and Vidhana Soudha illuminated at twilight',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~2 hrs transit',
          title: 'Vande Bharat Express to Mysuru',
        },
      },
      {
        id: 'mysuru',
        name: 'Mysuru',
        country: 'India',
        nights: 2,
        role: 'Royal Palace City',
        imageUrl: 'https://images.unsplash.com/photo-1600100397608-f010e42f9b20?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Illuminated golden domes of Mysore Palace in Karnataka',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~3 hrs transit',
          title: 'Western Ghats Road to Coorg',
        },
      },
      {
        id: 'coorg',
        name: 'Coorg (Madikeri)',
        country: 'India',
        nights: 3,
        role: 'Coffee Estates & Waterfalls',
        imageUrl: 'https://images.unsplash.com/photo-1587922546307-776227941871?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Mist rising over lush green coffee plantation hills in Coorg',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~6 hrs transit',
          title: 'Express Train to Hospet / Hampi',
        },
      },
      {
        id: 'hampi',
        name: 'Hampi',
        country: 'India',
        nights: 2,
        role: 'UNESCO Boulder Ruins',
        imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Stone chariot of Vijayanagara Empire standing in Hampi ruins',
      },
    ],
    suggestions: [
      {
        id: 'gokarna',
        name: 'Gokarna & Om Beach',
        region: 'Uttara Kannada, Karnataka',
        tag: 'Pristine Coastal Cliffs',
        description: 'Laid-back pilgrimage and beach haven with dramatic cliffs meeting the Arabian Sea.',
        imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  },
];

// -------------------------------------------------------------
// 2. CURATED TOP INTERNATIONAL DESTINATIONS (NORWAY, SWITZERLAND, ETC.)
// -------------------------------------------------------------
export const CURATED_INTERNATIONAL_DESTINATIONS: DestinationItem[] = [
  {
    id: 'norway',
    name: 'Norway (Oslo, Flåm, Bergen & Tromsø)',
    alias: 'Norway Fjords',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'Schengen Visa Required • ~15-30 Days Processing',
    defaultDurationDays: 10,
    seasonSummary: 'Optimal Season: Midnight Sun & Fjords (Jun-Aug) / Northern Lights (Sep-Mar)',
    defaultStops: [
      {
        id: 'oslo',
        name: 'Oslo',
        country: 'Norway',
        nights: 2,
        role: 'Capital & Fjord Gateway',
        imageUrl: 'https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Oslo Opera House resting on Oslofjord harbor waters',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~4 hrs 30 mins',
          title: 'Bergen Line Scenic High-Mountain Railway to Myrdal',
        },
      },
      {
        id: 'flam',
        name: 'Flåm & Sognefjord',
        country: 'Norway',
        nights: 2,
        role: 'Dramatic Fjord Rails & Glaciers',
        imageUrl: 'https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Flåm Railway winding down steep green cliffs into Aurlandsfjord',
        transitToNext: {
          mode: 'ferry',
          icon: 'directions_boat',
          duration: '~5 hrs transit',
          title: 'Sognefjord Express Catamaran to Bergen',
        },
      },
      {
        id: 'bergen',
        name: 'Bergen',
        country: 'Norway',
        nights: 3,
        role: 'Bryggen Wharf & Fjord Gateway',
        imageUrl: 'https://images.unsplash.com/photo-1520769669658-f07657f5a307?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Iconic colorful wooden merchant houses along Bryggen wharf Bergen',
        transitToNext: {
          mode: 'flight',
          icon: 'flight',
          duration: '~2 hrs transit',
          title: 'Direct Arctic Flight to Tromsø',
        },
      },
      {
        id: 'tromso',
        name: 'Tromsø',
        country: 'Norway',
        nights: 3,
        role: 'Arctic Capital & Northern Lights',
        imageUrl: 'https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Vibrant green Aurora Borealis dancing across snowy Arctic mountains in Tromsø',
      },
    ],
    suggestions: [
      {
        id: 'geiranger',
        name: 'Geirangerfjord',
        region: 'Møre og Romsdal, Norway',
        tag: 'UNESCO Fjord Wonder',
        description: 'Sheer granite cliffs and the famous Seven Sisters waterfalls rising out of sapphire waters.',
        imageUrl: 'https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'lofoten',
        name: 'Lofoten Islands',
        region: 'Nordland, Norway',
        tag: 'Arctic Archipelago',
        description: 'Dramatic jagged mountain peaks rising directly from the Norwegian Sea with red fishing cabins.',
        imageUrl: 'https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
      {
        id: 'preikestolen',
        name: 'Preikestolen (Pulpit Rock)',
        region: 'Stavanger, Norway',
        tag: 'Epic Fjord Clifftop',
        description: 'Flat-topped 604-meter rock plateau towering directly over Lysefjord.',
        imageUrl: 'https://images.unsplash.com/photo-1520769669658-f07657f5a307?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'switzerland',
    name: 'Switzerland (Zurich, Lucerne, Interlaken & Zermatt)',
    alias: 'Swiss Alpine Trail',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'Schengen Visa Required • ~15-30 Days Processing',
    defaultDurationDays: 10,
    seasonSummary: 'Optimal Season: Alpine Wildflowers (May-Sep) / World-Class Skiing (Dec-Apr)',
    defaultStops: [
      {
        id: 'zurich',
        name: 'Zurich',
        country: 'Switzerland',
        nights: 2,
        role: 'Lake City & Arrival Hub',
        imageUrl: 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Limmat River and historic twin spires of Grossmünster in Zurich',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~50 mins transit',
          title: 'SBB InterCity Rail to Lucerne',
        },
      },
      {
        id: 'lucerne',
        name: 'Lucerne & Mt. Pilatus',
        country: 'Switzerland',
        nights: 3,
        role: 'Chapel Bridge & Mountain Lake',
        imageUrl: 'https://images.unsplash.com/photo-1527668752968-14dc70a27c95?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Historic wooden Chapel Bridge in Lucerne with Lake Lucerne reflection',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~1 hr 50 mins',
          title: 'Luzern-Interlaken Express Panoramic Train',
        },
      },
      {
        id: 'interlaken',
        name: 'Interlaken & Jungfrau',
        country: 'Switzerland',
        nights: 3,
        role: 'Top of Europe & Lauterbrunnen',
        imageUrl: 'https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Lauterbrunnen valley with Staubbach waterfall framed by Swiss Alps',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~2 hrs 15 mins',
          title: 'Matterhorn Gotthard Bahn to Zermatt',
        },
      },
      {
        id: 'zermatt',
        name: 'Zermatt & Matterhorn',
        country: 'Switzerland',
        nights: 2,
        role: 'Car-Free Alpine Peak Sanctuary',
        imageUrl: 'https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Iconic pyramidal peak of the Matterhorn bathed in golden sunrise',
      },
    ],
    suggestions: [
      {
        id: 'geneva',
        name: 'Geneva & Lake Geneva',
        region: 'Lake Geneva Region',
        tag: 'Jet d\'Eau & Old Town',
        description: 'Cosmopolitan diplomatic enclave on the shores of Western Europe\'s largest alpine lake.',
        imageUrl: 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  },
  {
    id: 'france',
    name: 'France (Paris, Lyon & French Riviera)',
    alias: 'France Elegance',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'Schengen Visa Required • ~15-30 Days Processing',
    defaultDurationDays: 10,
    seasonSummary: 'Optimal Season: Spring Blooms (Apr-Jun) / Autumn Culture & Wine (Sep-Nov)',
    defaultStops: [
      {
        id: 'paris',
        name: 'Paris',
        country: 'France',
        nights: 4,
        role: 'City of Light & Art',
        imageUrl: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Eiffel Tower rising above Haussmann architecture and Seine River Paris',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~1 hr 57 mins',
          title: 'TGV InOui High-Speed Rail to Lyon',
        },
      },
      {
        id: 'lyon',
        name: 'Lyon',
        country: 'France',
        nights: 2,
        role: 'Gastronomy Capital & Renaissance',
        imageUrl: 'https://images.unsplash.com/photo-1524397031866-1c6f4949a2a7?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Colorful Renaissance facades along Saone river in Vieux Lyon',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~4 hrs 30 mins',
          title: 'TGV Mediterranean Rail to Nice',
        },
      },
      {
        id: 'nice',
        name: 'Nice & Côte d\'Azur',
        country: 'France',
        nights: 4,
        role: 'Mediterranean Coast & Promenade',
        imageUrl: 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Promenade des Anglais curving along turquoise waters of Nice France',
      },
    ],
    suggestions: [
      {
        id: 'monaco',
        name: 'Monaco & Monte Carlo',
        region: 'French Riviera',
        tag: 'Royal Principality',
        description: 'Glamorous harbor enclave with luxury yachts, casino palaces, and cliffside botanical gardens.',
        imageUrl: 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'thailand',
    name: 'Thailand (Bangkok, Chiang Mai & Phuket)',
    alias: 'Thailand Trails',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'Visa Exemption / 60-Day Free Entry for Indian Passports',
    defaultDurationDays: 10,
    seasonSummary: 'Optimal Season: Dry & Sunny Coastal Weather (Nov-Apr)',
    defaultStops: [
      {
        id: 'bangkok',
        name: 'Bangkok',
        country: 'Thailand',
        nights: 3,
        role: 'Golden Temples & Street Food',
        imageUrl: 'https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Wat Arun Temple of Dawn glistening across Chao Phraya River Bangkok',
        transitToNext: {
          mode: 'flight',
          icon: 'flight',
          duration: '~1 hr 15 mins',
          title: 'Domestic Flight to Chiang Mai',
        },
      },
      {
        id: 'chiang-mai',
        name: 'Chiang Mai',
        country: 'Thailand',
        nights: 3,
        role: 'Old City & Mountain Sanctuaries',
        imageUrl: 'https://images.unsplash.com/photo-1513415564515-763d91423bdd?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Wat Phra That Doi Suthep mountain temple overlooking Chiang Mai valley',
        transitToNext: {
          mode: 'flight',
          icon: 'flight',
          duration: '~2 hrs transit',
          title: 'Direct Island Flight to Phuket',
        },
      },
      {
        id: 'phuket',
        name: 'Phuket & Andaman Coast',
        country: 'Thailand',
        nights: 4,
        role: 'Island Beaches & Limestone Bays',
        imageUrl: 'https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Traditional wooden longtail boat moored in crystal turquoise bay Phuket',
      },
    ],
    suggestions: [
      {
        id: 'phi-phi',
        name: 'Phi Phi Islands',
        region: 'Krabi / Phuket',
        tag: 'Limestone Lagoon Paradise',
        description: 'Iconic Maya Bay limestone lagoons with coral reefs and towering sea karsts.',
        imageUrl: 'https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'vietnam',
    name: 'Vietnam (Hanoi, Ha Long Bay & Da Nang/Hoi An)',
    alias: 'Vietnam Wonders',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'eVisa Active • 30-90 Days Instant for Indian Passports',
    defaultDurationDays: 9,
    seasonSummary: 'Optimal Season: Favorable Mild Temperatures & Clear Skies (Oct-Apr)',
    defaultStops: [
      {
        id: 'hanoi',
        name: 'Hanoi',
        country: 'Vietnam',
        nights: 3,
        role: 'Old Quarter & French Colonial',
        imageUrl: 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Hanoi Old Quarter narrow streets bustling with coffee houses and lanterns',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~2 hrs 30 mins',
          title: 'Luxury Highway Transfer to Ha Long Marina',
        },
      },
      {
        id: 'halong-bay',
        name: 'Ha Long Bay',
        country: 'Vietnam',
        nights: 2,
        role: 'Emerald Sea & Limestone Karsts',
        imageUrl: 'https://images.unsplash.com/photo-1528127269322-539801943592?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Hundreds of limestone karst islands rising from emerald waters of Ha Long Bay',
        transitToNext: {
          mode: 'flight',
          icon: 'flight',
          duration: '~1 hr 20 mins',
          title: 'Coastal Flight to Da Nang',
        },
      },
      {
        id: 'hoi-an',
        name: 'Da Nang & Hoi An',
        country: 'Vietnam',
        nights: 4,
        role: 'Lantern Town & Marble Mountains',
        imageUrl: 'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Hoi An ancient river town illuminated by colorful silk lanterns at night',
      },
    ],
    suggestions: [
      {
        id: 'ba-na-hills',
        name: 'Ba Na Hills & Golden Bridge',
        region: 'Da Nang, Vietnam',
        tag: 'Giant Hands Bridge',
        description: 'Spectacular pedestrian bridge supported by two enormous stone hands over misty cliffs.',
        imageUrl: 'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'bali',
    name: 'Bali, Indonesia (Ubud, Seminyak & Nusa Penida)',
    alias: 'Bali Islands',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'Visa on Arrival (e-VOA) • 30 Days Instant for Indian Passports',
    defaultDurationDays: 8,
    seasonSummary: 'Optimal Season: Warm Tropical Sun & Gentle Ocean Swells (Apr-Oct)',
    defaultStops: [
      {
        id: 'ubud',
        name: 'Ubud',
        country: 'Indonesia',
        nights: 3,
        role: 'Rice Terraces & Jungle Sanctuaries',
        imageUrl: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Emerald green Tegalalang rice terraces stepping down jungle valley in Ubud Bali',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~1 hr 30 mins',
          title: 'Private Chauffeur to Coastal Seminyak',
        },
      },
      {
        id: 'seminyak',
        name: 'Seminyak & Canggu',
        country: 'Indonesia',
        nights: 3,
        role: 'Sunset Coast & Beach Clubs',
        imageUrl: 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Golden sunset across Seminyak beach with rolling Indian Ocean surf',
        transitToNext: {
          mode: 'ferry',
          icon: 'directions_boat',
          duration: '~45 mins transit',
          title: 'Sanur Fast Boat to Nusa Penida Island',
        },
      },
      {
        id: 'nusa-penida',
        name: 'Nusa Penida',
        country: 'Indonesia',
        nights: 2,
        role: 'Kelingking Cliff & Coastal Wonders',
        imageUrl: 'https://images.unsplash.com/photo-1578469550956-0e16b69c6a3d?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Dramatic T-Rex shaped coastal promontory of Kelingking Beach Nusa Penida',
      },
    ],
    suggestions: [
      {
        id: 'uluwatu',
        name: 'Uluwatu Temple & Sunset Kecak Dance',
        region: 'Bukit Peninsula, Bali',
        tag: 'Clifftop Sea Temple',
        description: '70-meter sea cliff temple with spectacular sunset Kecak fire dance overlooking the ocean.',
        imageUrl: 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'uae',
    name: 'Dubai & UAE (Dubai Downtown, Marina & Abu Dhabi)',
    alias: 'Dubai Splendor',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: '30-Day Tourist Visa / eVisa Active for Indian Passports',
    defaultDurationDays: 7,
    seasonSummary: 'Optimal Season: Perfect Mild Winter & Beach Weather (Nov-Mar)',
    defaultStops: [
      {
        id: 'dubai',
        name: 'Dubai',
        country: 'United Arab Emirates',
        nights: 4,
        role: 'Futuristic Skyscrapers & Souks',
        imageUrl: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Burj Khalifa rising above the Dubai Fountain and downtown skyline',
        transitToNext: {
          mode: 'car',
          icon: 'directions_car',
          duration: '~1 hr 15 mins',
          title: 'Luxury Highway Transfer to Abu Dhabi',
        },
      },
      {
        id: 'abu-dhabi',
        name: 'Abu Dhabi',
        country: 'United Arab Emirates',
        nights: 3,
        role: 'Grand Mosque & Cultural Louvre',
        imageUrl: 'https://images.unsplash.com/photo-1518684079-3c830dcef090?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'White marble domes and minarets of Sheikh Zayed Grand Mosque Abu Dhabi',
      },
    ],
    suggestions: [
      {
        id: 'desert-safari',
        name: 'Red Dune Desert Safari & Bedouin Camp',
        region: 'Dubai, UAE',
        tag: 'Dune Bashing & Stargazing',
        description: 'Thrilling 4x4 dune bashing across crimson desert sands followed by traditional barbecue and stargazing.',
        imageUrl: 'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&auto=format&fit=crop&q=80',
        actionLabel: 'Add as Day Trip',
        isDayTrip: true,
      },
    ],
  },
  {
    id: 'uk',
    name: 'United Kingdom (London, Edinburgh & Scottish Highlands)',
    alias: 'British Heritage',
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: 'UK Standard Visitor Visa Required • ~3 Weeks Processing',
    defaultDurationDays: 9,
    seasonSummary: 'Optimal Season: Long Summer Daylight & Castle Festivals (May-Sep)',
    defaultStops: [
      {
        id: 'london',
        name: 'London',
        country: 'United Kingdom',
        nights: 4,
        role: 'Royal Monuments & Thames',
        imageUrl: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Big Ben clock tower and Westminster Bridge over Thames River London',
        transitToNext: {
          mode: 'train',
          icon: 'train',
          duration: '~4 hrs 20 mins',
          title: 'LNER High-Speed Rail along East Coast to Edinburgh',
        },
      },
      {
        id: 'edinburgh',
        name: 'Edinburgh & Scottish Highlands',
        country: 'United Kingdom',
        nights: 5,
        role: 'Castle Clifftops & Lochs',
        imageUrl: 'https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?w=800&auto=format&fit=crop&q=80',
        imageAlt: 'Historic Edinburgh Castle sitting on volcanic Castle Rock Scotland',
      },
    ],
    suggestions: [
      {
        id: 'loch-ness',
        name: 'Loch Ness & Isle of Skye',
        region: 'Highlands, Scotland',
        tag: 'Mythic Lochs & Glens',
        description: 'Dramatic mountain glens and ancient ruins of Urquhart Castle over deep waters.',
        imageUrl: 'https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  },
];

// Combine all curated items with existing Japan, Ladakh, Italy, Kerala
export const PRECONFIGURED_DESTINATIONS: DestinationItem[] = PRECONFIGURED_CIRCUITS.map((c) => ({
  id: c.id,
  name: c.name,
  alias: c.alias,
  scope: c.scope,
  type: (c.scope === 'DOMESTIC' ? 'STATE' : 'COUNTRY') as 'STATE' | 'COUNTRY',
  visaStatus: c.visaStatus,
  defaultDurationDays: c.defaultDurationDays,
  seasonSummary: c.seasonInsights['autumn'] || 'Optimal Season: Pleasant Weather & Mild Sunshine',
  defaultStops: c.defaultStops,
  suggestions: c.suggestions,
}));

export const ALL_CURATED_DESTINATIONS: DestinationItem[] = [
  ...PRECONFIGURED_DESTINATIONS,
  ...CURATED_INTERNATIONAL_DESTINATIONS,
  ...DOMESTIC_DESTINATIONS,
];

// Helper to compute unified, accurate visa status for sovereign countries for Indian citizens
export function getCountryVisaStatus(c: { name: string; region: string; is_schengen: boolean }): string {
  const nameLower = c.name.toLowerCase();
  if (nameLower === 'nepal' || nameLower === 'bhutan') {
    return 'Visa Free • Freedom of Movement for Indian Citizens (No Visa Needed)';
  }
  if (c.is_schengen) {
    return 'Schengen Visa Required • ~15-30 Days Processing';
  }
  if (c.region === 'Asia') {
    return 'eVisa or Visa on Arrival Available for Indian Passports';
  }
  return 'International Destination • Tourist Visa / eVisa Active';
}

// Helper to generate dynamic fallback stops for any of the 36 Indian states & UTs
export function generateDomesticFallback(stateOrUtName: string): DestinationItem | null {
  const query = stateOrUtName.toLowerCase().trim();
  const primaryQuery = query.replace(/\s*\([^)]*\).*/, '').trim();

  const found = (indianStatesUts as Array<{
    id: string;
    name: string;
    type: 'STATE' | 'UT';
    capital: string;
    top_cities: string[];
    alias: string;
    season: string;
  }>).find((s) => {
    const sNameLower = s.name.toLowerCase();
    const sIdLower = s.id.toLowerCase();
    return (
      sNameLower === query ||
      sNameLower === primaryQuery ||
      sIdLower === query ||
      sIdLower === `in-${query}` ||
      sIdLower === primaryQuery ||
      s.alias.toLowerCase() === query ||
      s.alias.toLowerCase() === primaryQuery ||
      (primaryQuery.length >= 4 && sNameLower.startsWith(primaryQuery))
    );
  });

  if (!found) return null;

  const cities = found.top_cities.length > 0 ? found.top_cities : [found.capital || found.name];
  const stops: RouteStop[] = cities.map((city, idx) => ({
    id: `${found.id}-stop-${idx + 1}`,
    name: city,
    country: 'India',
    region: found.name,
    nights: idx === 0 ? 3 : 2,
    role: idx === 0 ? 'State Capital & Arrival Hub' : 'Scenic Gateway & Heritage Quarter',
    imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
    imageAlt: `${city} in ${found.name}`,
    transitToNext:
      idx < cities.length - 1
        ? {
            mode: 'transit',
            icon: 'directions_transit',
            duration: '~2 hrs transit',
            title: `Scenic Regional Express to ${cities[idx + 1]}`,
          }
        : undefined,
  }));

  const totalNights = stops.reduce((acc, s) => acc + s.nights, 0);

  return {
    id: found.id,
    name: `${found.name} (${cities.join(', ')})`,
    alias: found.alias,
    scope: 'DOMESTIC',
    type: found.type,
    visaStatus: getDomesticPermitStatus(found.name) || getDomesticPermitStatus(found.id),
    defaultDurationDays: Math.max(7, totalNights),
    seasonSummary: `Optimal Season: ${found.season}`,
    defaultStops: stops,
    suggestions: [
      {
        id: `${found.id}-suggest-1`,
        name: `${found.capital} Cultural & Heritage Sanctuaries`,
        region: found.name,
        tag: 'Heritage & Culture',
        description: `Explore the vibrant local markets, ancient architecture, and cultural traditions of ${found.name}.`,
        imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  };
}

// Helper to generate dynamic fallback stops for any of the 250 sovereign countries
export function generateCountryFallback(countryName: string): DestinationItem | null {
  const cLower = countryName.toLowerCase().trim();
  const cleanCLower = cLower.replace(/\s*\([^)]*\).*/, '').trim();
  const cId = cleanCLower.replace(/\s+/g, '-');

  const cData = (generatedCountries as Array<{
    code: string;
    name: string;
    capital: string;
    region: string;
    subregion: string;
    is_schengen: boolean;
    top_cities: string[];
  }>).find((c) => {
    const nameLower = c.name.toLowerCase();
    const countryId = nameLower.replace(/\s+/g, '-');
    return (
      nameLower === cleanCLower ||
      countryId === cId ||
      countryId === cLower ||
      nameLower === cLower ||
      (c.code && c.code.toLowerCase() === cleanCLower) ||
      (cleanCLower.length >= 4 && nameLower.startsWith(cleanCLower))
    );
  });

  if (!cData) return null;

  const visa = getCountryVisaStatus(cData);

  const cities = cData.top_cities.length > 0 ? cData.top_cities : [cData.capital || cData.name];
  const stops: RouteStop[] = cities.map((city, idx) => ({
    id: `${cData.code.toLowerCase()}-stop-${idx + 1}`,
    name: city,
    country: cData.name,
    nights: idx === 0 ? 3 : 2,
    role: idx === 0 ? 'Capital & Arrival Hub' : 'Regional Gateway & Cultural Heart',
    imageUrl: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80',
    imageAlt: `${city} in ${cData.name}`,
    transitToNext:
      idx < cities.length - 1
        ? {
            mode: 'transit',
            icon: 'directions_transit',
            duration: '~2 hrs transit',
            title: `Scenic Regional Connection to ${cities[idx + 1]}`,
          }
        : undefined,
  }));

  const totalNights = stops.reduce((acc, s) => acc + s.nights, 0);

  return {
    id: cData.name.toLowerCase().replace(/\s+/g, '-'),
    name: `${cData.name} (${cities.join(', ')})`,
    alias: `${cData.name} Circuit`,
    scope: 'INTERNATIONAL',
    type: 'COUNTRY',
    visaStatus: visa,
    defaultDurationDays: Math.max(7, totalNights),
    seasonSummary: 'Optimal Season: Favorable Mild Temperatures & Pleasant Sightseeing Conditions',
    defaultStops: stops,
    suggestions: [
      {
        id: `${cData.code.toLowerCase()}-suggest-1`,
        name: `${cData.name} Highlights & Historic Quarter`,
        region: cData.name,
        tag: 'Cultural Heritage',
        description: `Explore the vibrant architectural landmarks, historic museums, and local cuisine of ${cData.name}.`,
        imageUrl: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  };
}

// Helper to generate dynamic fallback stops for any Indian city from the API dataset
export function generateDomesticCityFallback(cityInput: string): DestinationItem | null {
  const q = cityInput.toLowerCase().trim();
  const cleanQ = q.startsWith('in-') ? q.slice(3).replace(/-/g, ' ') : q;
  const primaryCleanQ = cleanQ.replace(/\s*\([^)]*\).*/, '').trim();

  const cityList = (indiaPlacesData as {
    cities: Array<{
      id: string;
      name: string;
      state_name: string;
      state_code: string;
      state_id: string;
      scope: 'DOMESTIC';
      is_popular: boolean;
    }>;
  }).cities;

  const cityMatch = cityList.find((c) => {
    const cNameLower = c.name.toLowerCase();
    const cIdLower = c.id.toLowerCase();
    // 1. Exact match on ID
    if (cIdLower === q || cIdLower === `in-${q}` || cIdLower === `in-${primaryCleanQ.replace(/\s+/g, '-')}`) {
      return true;
    }
    // 2. Exact match on name
    if (cNameLower === cleanQ || cNameLower === primaryCleanQ) {
      return true;
    }
    // 3. Exact city with state: "mumbai, maharashtra" or "mumbai (maharashtra, india)"
    if (cleanQ === `${cNameLower}, ${c.state_name.toLowerCase()}` || cleanQ.startsWith(`${cNameLower} (`)) {
      return true;
    }
    // 4. Clean prefix match ONLY if input is at least 4 characters
    if (primaryCleanQ.length >= 4 && cNameLower.startsWith(primaryCleanQ)) {
      return true;
    }
    return false;
  });

  if (!cityMatch) return null;

  const statesList = (indiaPlacesData as {
    states: Array<{
      id: string;
      name: string;
      code: string;
      type: string;
      popular_cities: string[];
      cities: string[];
    }>;
  }).states;

  const stateRecord = statesList.find(
    (s) => s.name.toLowerCase() === cityMatch.state_name.toLowerCase() || s.code === cityMatch.state_code
  );

  const siblingCities = stateRecord
    ? stateRecord.popular_cities.filter((c) => c.toLowerCase() !== cityMatch.name.toLowerCase()).slice(0, 3)
    : [];

  const routeCityNames = [cityMatch.name, ...siblingCities];
  const stops: RouteStop[] = routeCityNames.map((city, idx) => ({
    id: `in-${city.toLowerCase().replace(/\s+/g, '-')}-stop-${idx + 1}`,
    name: city,
    country: 'India',
    region: cityMatch.state_name,
    nights: idx === 0 ? 3 : 2,
    role: idx === 0 ? 'Primary City & Arrival Quarter' : 'Regional Gateway & Scenic Stop',
    imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
    imageAlt: `${city} in ${cityMatch.state_name}, India`,
    transitToNext:
      idx < routeCityNames.length - 1
        ? {
            mode: 'transit',
            icon: 'directions_transit',
            duration: '~2 hrs 30 mins',
            title: `Scenic Regional Connection to ${routeCityNames[idx + 1]}`,
          }
        : undefined,
  }));

  const totalNights = stops.reduce((acc, s) => acc + s.nights, 0);

  return {
    id: cityMatch.id,
    name: `${cityMatch.name} (${cityMatch.state_name}, India)`,
    alias: `${cityMatch.name} Trail`,
    scope: 'DOMESTIC',
    type: 'STATE',
    visaStatus: getDomesticPermitStatus(cityMatch.name) || getDomesticPermitStatus(cityMatch.state_name),
    defaultDurationDays: Math.max(5, totalNights),
    seasonSummary: `Optimal Season: Pleasant Weather & Regional Explorations in ${cityMatch.state_name}`,
    defaultStops: stops,
    suggestions: [
      {
        id: `${cityMatch.id}-suggest-1`,
        name: `${cityMatch.name} Heritage Quarter & Cultural Bazaars`,
        region: `${cityMatch.state_name}, India`,
        tag: 'Heritage & Local Flavors',
        description: `Explore the vibrant local markets, historic monuments, and authentic regional cuisine of ${cityMatch.name}.`,
        imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
        actionLabel: '+ Add Stop',
      },
    ],
  };
}

// Internal single destination resolution function
export function resolveSingleDestinationData(
  destinationInput: string,
  scopeHint?: 'DOMESTIC' | 'INTERNATIONAL'
): DestinationItem {
  if (!destinationInput || !destinationInput.trim()) {
    return scopeHint === 'DOMESTIC'
      ? ALL_CURATED_DESTINATIONS.find((d) => d.scope === 'DOMESTIC') || ALL_CURATED_DESTINATIONS[0]
      : ALL_CURATED_DESTINATIONS[0];
  }
  const query = destinationInput.toLowerCase().trim();
  const primaryQuery = query.replace(/\s*\([^)]*\).*/, '').trim();

  // Helper to safely match curated destinations without accidental substring collisions (e.g. 'uk' inside 'lukla')
  const findCurated = (targetScope?: 'DOMESTIC' | 'INTERNATIONAL') => {
    return ALL_CURATED_DESTINATIONS.find((d) => {
      if (targetScope && d.scope !== targetScope) return false;
      const id = d.id.toLowerCase();
      const alias = d.alias.toLowerCase();
      const name = d.name.toLowerCase();
      const primaryName = name.replace(/\s*\([^)]*\).*/, '').trim().toLowerCase();

      // 1. Exact match on ID, alias, name, or primary name
      if (
        query === id ||
        query === alias ||
        query === name ||
        primaryQuery === id ||
        primaryQuery === primaryName ||
        primaryQuery === alias
      ) {
        return true;
      }

      // 2. Strict ID matching with word boundaries to prevent 'uk' matching inside words like 'lukla'
      if (id.length <= 3) {
        const idRegex = new RegExp(`(^|\\b|\\s|\\-)${id}(\\b|\\s|\\-|$)`, 'i');
        if (idRegex.test(primaryQuery) || idRegex.test(query)) {
          return true;
        }
      } else {
        if (
          primaryQuery.includes(id) ||
          id.includes(primaryQuery) ||
          query.includes(alias) ||
          alias.includes(primaryQuery)
        ) {
          return true;
        }
      }

      return false;
    });
  };

  // If scope is explicitly INTERNATIONAL:
  if (scopeHint === 'INTERNATIONAL') {
    // 1. Curated international match
    const curatedIntl = findCurated('INTERNATIONAL');
    if (curatedIntl) return curatedIntl;

    // 2. International sovereign country fallback
    const countryFallback = generateCountryFallback(destinationInput);
    if (countryFallback) return countryFallback;

    // 3. Default international destination
    return ALL_CURATED_DESTINATIONS.find((d) => d.scope === 'INTERNATIONAL') || ALL_CURATED_DESTINATIONS[0];
  }

  // If scope is explicitly DOMESTIC:
  if (scopeHint === 'DOMESTIC') {
    // 1. Curated domestic match
    const curatedDom = findCurated('DOMESTIC');
    if (curatedDom) return curatedDom;

    // 2. Direct match in Indian Cities from the dataset
    const cityFallback = generateDomesticCityFallback(destinationInput);
    if (cityFallback) return cityFallback;

    // 3. Direct match in Indian States & UTs
    const domesticFallback = generateDomesticFallback(destinationInput);
    if (domesticFallback) return domesticFallback;

    // 4. Default domestic destination
    return ALL_CURATED_DESTINATIONS.find((d) => d.scope === 'DOMESTIC') || ALL_CURATED_DESTINATIONS[0];
  }

  // If no scopeHint is provided:
  // 1. Direct exact match in curated destinations
  const curatedMatch = findCurated();
  if (curatedMatch) return curatedMatch;

  // 2. Direct exact country match from static dataset
  const countryFallback = generateCountryFallback(destinationInput);
  if (countryFallback) return countryFallback;

  // 3. Direct match in Indian Cities
  const cityFallback = generateDomesticCityFallback(destinationInput);
  if (cityFallback) return cityFallback;

  // 4. Fallback dynamically generated domestic Indian state or UT
  const domesticFallback = generateDomesticFallback(destinationInput);
  if (domesticFallback) return domesticFallback;

  // 5. Default curated destination
  return ALL_CURATED_DESTINATIONS[0];
}

// Helper to cleanly split destination strings without breaking commas inside parentheses
export function splitDestinationsString(str: string): string[] {
  if (!str) return [];
  const parts: string[] = [];
  let current = '';
  let parenDepth = 0;
  for (const char of str) {
    if (char === '(') parenDepth++;
    else if (char === ')') parenDepth = Math.max(0, parenDepth - 1);

    if (char === ',' && parenDepth === 0) {
      if (current.trim()) parts.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

// Master resolution function: given any destination string, array, or multi-destination input, resolves accurate stops
export function resolveDestinationData(
  destinationInput: string | string[],
  scopeHint?: 'DOMESTIC' | 'INTERNATIONAL'
): DestinationItem {
  if (!destinationInput || (Array.isArray(destinationInput) && destinationInput.length === 0)) {
    return resolveSingleDestinationData('', scopeHint);
  }

  // Parse destinations into individual parts respecting parentheses
  const rawParts = Array.isArray(destinationInput)
    ? destinationInput.map((s) => s.trim()).filter(Boolean)
    : splitDestinationsString(destinationInput);

  if (rawParts.length <= 1) {
    return resolveSingleDestinationData(rawParts[0] || '', scopeHint);
  }

  // Multiple destinations provided
  const items = rawParts.map((p) => resolveSingleDestinationData(p, scopeHint));

  const combinedStops: RouteStop[] = [];
  const combinedSuggestions: DestinationSuggestion[] = [];
  let stopCounter = 1;

  items.forEach((item, itemIdx) => {
    // Take top 2 stops from each destination (or all if <= 2)
    const stopsToTake = item.defaultStops.slice(0, 2);
    stopsToTake.forEach((stop, stopIdx) => {
      const isLastOfCurrentItem = stopIdx === stopsToTake.length - 1;
      const isVeryLastStop = itemIdx === items.length - 1 && isLastOfCurrentItem;

      let transit = stop.transitToNext;
      if (isLastOfCurrentItem && !isVeryLastStop) {
        const nextItem = items[itemIdx + 1];
        const nextFirstStop = nextItem.defaultStops[0];
        transit = {
          mode: 'transit',
          icon: 'alt_route',
          duration: '~3-4 hrs transit',
          title: `Cross-Region Scenic Connection to ${nextFirstStop?.name || nextItem.alias}`,
        };
      } else if (isVeryLastStop) {
        transit = undefined;
      }

      combinedStops.push({
        ...stop,
        id: `${stop.id}-multi-${stopCounter++}`,
        transitToNext: transit,
      });
    });

    if (item.suggestions) {
      combinedSuggestions.push(...item.suggestions.slice(0, 2));
    }
  });

  const totalNights = combinedStops.reduce((sum, s) => sum + s.nights, 0);
  const cleanAliases = items.map((it) => it.alias || it.name.replace(/\s*\([^)]*\).*/, '').trim());
  const cleanNames = items.map((it) => it.name.replace(/\s*\([^)]*\).*/, '').trim());

  return {
    id: `multi-${items.map((it) => it.id).join('-')}`,
    name: cleanNames.join(', '),
    alias: `${cleanAliases.join(' & ')} Trail`,
    scope: scopeHint || items[0].scope,
    type: 'CIRCUIT',
    visaStatus: getMultiDestinationVisaVerdict(rawParts, scopeHint || items[0].scope),
    defaultDurationDays: Math.max(7, totalNights),
    seasonSummary: items[0].seasonSummary || 'Optimal Season: Multi-Region Travel & Pleasant Conditions',
    defaultStops: combinedStops,
    suggestions: combinedSuggestions,
  };
}

function getThematicImageUrl(stateOrCountry: string): string {
  const s = stateOrCountry.toLowerCase();
  if (s.includes('rajasthan')) return 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80';
  if (s.includes('kerala')) return 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&auto=format&fit=crop&q=80';
  if (s.includes('goa')) return 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80';
  if (s.includes('himachal') || s.includes('uttarakhand') || s.includes('ladakh') || s.includes('kashmir')) {
    return 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80';
  }
  if (s.includes('tamil') || s.includes('karnataka')) {
    return 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&auto=format&fit=crop&q=80';
  }
  if (s.includes('norway')) return 'https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=800&auto=format&fit=crop&q=80';
  if (s.includes('japan')) return 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&auto=format&fit=crop&q=80';
  if (s.includes('italy')) return 'https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=800&auto=format&fit=crop&q=80';
  if (s.includes('switzerland')) return 'https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=800&auto=format&fit=crop&q=80';
  if (s.includes('france')) return 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80';
  return 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80';
}

// Internal single destination contextual city retriever
export function getContextualCitiesForSingleDestination(destinationInput: string): ContextualCityItem[] {
  if (!destinationInput || !destinationInput.trim()) {
    return [];
  }
  const q = destinationInput.toLowerCase().trim();

  // 1. Check if destination corresponds to an Indian state or UT
  const stateRecord = (indiaPlacesData.states as Array<{
    id: string;
    name: string;
    code: string;
    type: string;
    popular_cities: string[];
    cities: string[];
  }>).find(
    (s) =>
      s.name.toLowerCase() === q ||
      q.includes(s.name.toLowerCase()) ||
      s.name.toLowerCase().includes(q) ||
      s.id === q ||
      q.includes(s.id)
  );

  if (stateRecord) {
    const popularSet = new Set(stateRecord.popular_cities.map((c) => c.toLowerCase()));
    const stateCities = stateRecord.cities.map((cityName) => {
      const isPop = popularSet.has(cityName.toLowerCase());
      return {
        id: `in-${cityName.toLowerCase().replace(/\s+/g, '-')}`,
        name: cityName,
        region: `${stateRecord.name}, India`,
        country: 'India',
        isPopular: isPop,
        role: isPop ? 'Iconic Regional Hub & Heritage Quarter' : 'Scenic Gateway & Local Settlement',
        imageUrl: getThematicImageUrl(stateRecord.name),
        imageAlt: `${cityName} in ${stateRecord.name}, India`,
      };
    });

    return stateCities.sort((a, b) => {
      if (a.isPopular && !b.isPopular) return -1;
      if (!a.isPopular && b.isPopular) return 1;
      return a.name.localeCompare(b.name);
    });
  }

  // 2. Check if destination corresponds to an Indian City (e.g. Udaipur) -> return sibling cities in its parent state
  const cityMatch = (indiaPlacesData.cities as Array<{
    id: string;
    name: string;
    state_name: string;
    state_code: string;
    state_id: string;
  }>).find(
    (c) =>
      c.name.toLowerCase() === q ||
      c.id.toLowerCase() === q ||
      q.includes(c.name.toLowerCase())
  );

  if (cityMatch) {
    return getContextualCitiesForSingleDestination(cityMatch.state_name);
  }

  // 3. Check if destination corresponds to a curated international circuit
  const curatedMatch = ALL_CURATED_DESTINATIONS.find((d) => {
    const dId = d.id.toLowerCase();
    const dName = d.name.toLowerCase();
    const dAlias = d.alias.toLowerCase();
    return q === dId || q.includes(dId) || dId.includes(q) || q.includes(dAlias) || dName.includes(q);
  });

  if (curatedMatch && curatedMatch.scope === 'INTERNATIONAL') {
    const items: ContextualCityItem[] = [];
    const added = new Set<string>();

    for (const stop of curatedMatch.defaultStops) {
      if (!added.has(stop.name.toLowerCase())) {
        added.add(stop.name.toLowerCase());
        items.push({
          id: stop.id,
          name: stop.name,
          region: stop.region || curatedMatch.name,
          country: stop.country,
          isPopular: true,
          role: stop.role,
          imageUrl: stop.imageUrl,
          imageAlt: stop.imageAlt,
        });
      }
    }

    for (const sugg of curatedMatch.suggestions) {
      if (!added.has(sugg.name.toLowerCase())) {
        added.add(sugg.name.toLowerCase());
        items.push({
          id: sugg.id,
          name: sugg.name,
          region: sugg.region,
          country: curatedMatch.name,
          isPopular: true,
          role: sugg.tag,
          imageUrl: sugg.imageUrl,
          imageAlt: sugg.imageAlt,
        });
      }
    }

    const countryData = (generatedCountries as Array<{
      name: string;
      top_cities: string[];
      region: string;
    }>).find(
      (c) =>
        c.name.toLowerCase() === curatedMatch.name.toLowerCase() ||
        curatedMatch.name.toLowerCase().includes(c.name.toLowerCase())
    );

    if (countryData && countryData.top_cities) {
      for (const cName of countryData.top_cities) {
        if (!added.has(cName.toLowerCase())) {
          added.add(cName.toLowerCase());
          items.push({
            id: `intl-${cName.toLowerCase().replace(/\s+/g, '-')}`,
            name: cName,
            region: `${countryData.name}, ${countryData.region}`,
            country: countryData.name,
            isPopular: false,
            role: 'Regional Gateway & Cultural Quarter',
            imageUrl: curatedMatch.defaultStops[0]?.imageUrl || getThematicImageUrl(countryData.name),
            imageAlt: `${cName} in ${countryData.name}`,
          });
        }
      }
    }

    return items;
  }

  // 4. Check in generatedCountries directly for international country
  const sovereignMatch = (generatedCountries as Array<{
    name: string;
    capital: string;
    region: string;
    top_cities: string[];
  }>).find(
    (c) =>
      c.name.toLowerCase() === q ||
      q.includes(c.name.toLowerCase()) ||
      c.name.toLowerCase().includes(q)
  );

  if (sovereignMatch) {
    const items: ContextualCityItem[] = [];
    const added = new Set<string>();

    const candidateCities = [
      sovereignMatch.capital,
      ...(sovereignMatch.top_cities || []),
    ].filter(Boolean);

    for (const cName of candidateCities) {
      if (!added.has(cName.toLowerCase())) {
        added.add(cName.toLowerCase());
        items.push({
          id: `intl-${cName.toLowerCase().replace(/\s+/g, '-')}`,
          name: cName,
          region: `${sovereignMatch.name}, ${sovereignMatch.region}`,
          country: sovereignMatch.name,
          isPopular: cName === sovereignMatch.capital,
          role: cName === sovereignMatch.capital ? 'Capital & Arrival Hub' : 'Scenic Gateway & Cultural Quarter',
          imageUrl: getThematicImageUrl(sovereignMatch.name),
          imageAlt: `${cName} in ${sovereignMatch.name}`,
        });
      }
    }
    return items;
  }

  return [];
}

// Master contextual city resolver supporting single or multi-destination input
export function getContextualCitiesForDestination(
  destinationInput: string | string[]
): ContextualCityItem[] {
  if (!destinationInput || (Array.isArray(destinationInput) && destinationInput.length === 0)) {
    return [];
  }

  const rawParts = Array.isArray(destinationInput)
    ? destinationInput.map((s) => s.trim()).filter(Boolean)
    : splitDestinationsString(destinationInput);

  if (rawParts.length <= 1) {
    return getContextualCitiesForSingleDestination(rawParts[0] || '');
  }

  const combined: ContextualCityItem[] = [];
  const seen = new Set<string>();

  for (const part of rawParts) {
    const partCities = getContextualCitiesForSingleDestination(part);
    for (const city of partCities) {
      const key = city.name.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        combined.push(city);
      }
    }
  }

  return combined;
}

// Autocomplete search across all 250 countries + all 36 Indian states & UTs + 4,200 Indian cities + curated circuits
export function searchAllDestinations(
  query: string,
  scopeFilter?: 'DOMESTIC' | 'INTERNATIONAL'
): Array<{
  id: string;
  title: string;
  subtitle: string;
  scope: 'DOMESTIC' | 'INTERNATIONAL';
  visaStatus: string;
}> {
  const q = query.toLowerCase().trim();
  const results: Array<{
    id: string;
    title: string;
    subtitle: string;
    scope: 'DOMESTIC' | 'INTERNATIONAL';
    visaStatus: string;
  }> = [];

  const addedIds = new Set<string>();

  const places = indiaPlacesData as {
    states: Array<{
      id: string;
      name: string;
      code: string;
      type: string;
      popular_cities: string[];
      cities: string[];
    }>;
    popular_destinations: Array<{
      id: string;
      name: string;
      state_name: string;
      state_code: string;
      state_id: string;
    }>;
    cities: Array<{
      id: string;
      name: string;
      state_name: string;
      state_code: string;
      state_id: string;
      is_popular: boolean;
    }>;
  };

  const allowDomestic = !scopeFilter || scopeFilter === 'DOMESTIC';
  const allowInternational = !scopeFilter || scopeFilter === 'INTERNATIONAL';

  if (!q) {
    // 1. Featured curated destinations
    for (const d of ALL_CURATED_DESTINATIONS) {
      if (
        ((allowDomestic && d.scope === 'DOMESTIC') ||
          (allowInternational && d.scope === 'INTERNATIONAL')) &&
        !addedIds.has(d.id)
      ) {
        addedIds.add(d.id);
        results.push({
          id: d.id,
          title: d.alias,
          subtitle: d.name,
          scope: d.scope,
          visaStatus: d.visaStatus,
        });
      }
    }

    // 2. Featured Indian states / UTs (if domestic allowed)
    if (allowDomestic) {
      for (const s of (indianStatesUts as Array<{ id: string; name: string; alias: string; top_cities: string[] }>).slice(0, 6)) {
        if (!addedIds.has(s.id)) {
          addedIds.add(s.id);
          results.push({
            id: s.id,
            title: s.name,
            subtitle: `${s.alias} • ${s.top_cities.slice(0, 3).join(', ')}`,
            scope: 'DOMESTIC',
            visaStatus: getDomesticPermitStatus(s.name) || getDomesticPermitStatus(s.id),
          });
        }
      }

      // 3. Iconic Indian tourist cities
      for (const c of places.popular_destinations.slice(0, 4)) {
        if (!addedIds.has(c.id)) {
          addedIds.add(c.id);
          results.push({
            id: c.id,
            title: c.name,
            subtitle: `City in ${c.state_name}, India`,
            scope: 'DOMESTIC',
            visaStatus: getDomesticPermitStatus(c.name) || getDomesticPermitStatus(c.state_name),
          });
        }
      }
    }

    // 4. Featured International sovereign countries (if international allowed)
    if (allowInternational) {
      for (const c of (generatedCountries as Array<{ code: string; name: string; capital: string; region: string; is_schengen: boolean }>).slice(0, 6)) {
        const cId = c.name.toLowerCase().replace(/\s+/g, '-');
        if (!addedIds.has(cId)) {
          addedIds.add(cId);
          results.push({
            id: cId,
            title: c.name,
            subtitle: `${c.capital ? c.capital + ', ' : ''}${c.region}`,
            scope: 'INTERNATIONAL',
            visaStatus: getCountryVisaStatus(c),
          });
        }
      }
    }

    return results.slice(0, 16);
  }

  // Active query:
  // 1. Curated destinations match
  for (const d of ALL_CURATED_DESTINATIONS) {
    if (
      ((allowDomestic && d.scope === 'DOMESTIC') ||
        (allowInternational && d.scope === 'INTERNATIONAL')) &&
      (d.name.toLowerCase().includes(q) ||
        d.alias.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q) ||
        d.defaultStops.some((s) => s.name.toLowerCase().includes(q)))
    ) {
      if (!addedIds.has(d.id)) {
        addedIds.add(d.id);
        results.push({
          id: d.id,
          title: d.alias,
          subtitle: d.name,
          scope: d.scope,
          visaStatus: d.visaStatus,
        });
      }
    }
  }

  // 2. Indian States & UTs match (if domestic allowed)
  if (allowDomestic) {
    for (const s of indianStatesUts) {
      if (
        s.name.toLowerCase().includes(q) ||
        s.alias.toLowerCase().includes(q) ||
        s.top_cities.some((c: string) => c.toLowerCase().includes(q))
      ) {
        if (!addedIds.has(s.id)) {
          addedIds.add(s.id);
          results.push({
            id: s.id,
            title: s.name,
            subtitle: `${s.alias} • ${s.top_cities.slice(0, 3).join(', ')}`,
            scope: 'DOMESTIC',
            visaStatus: getDomesticPermitStatus(s.name) || getDomesticPermitStatus(s.id),
          });
        }
      }
    }

    // 3. Indian Cities match
    for (const c of places.cities) {
      if (results.length >= 25) break;
      const nameLower = c.name.toLowerCase();
      if (nameLower.startsWith(q) || nameLower.includes(q)) {
        if (!addedIds.has(c.id)) {
          addedIds.add(c.id);
          results.push({
            id: c.id,
            title: c.name,
            subtitle: `City in ${c.state_name}, India`,
            scope: 'DOMESTIC',
            visaStatus: getDomesticPermitStatus(c.name) || getDomesticPermitStatus(c.state_name),
          });
        }
      }
    }
  }

  // 4. Sovereign Countries from static dataset (if international allowed)
  if (allowInternational) {
    for (const c of generatedCountries) {
      if (results.length >= 25) break;
      const cNameLower = c.name.toLowerCase();
      if (
        cNameLower.startsWith(q) ||
        cNameLower.includes(q) ||
        (c.capital && c.capital.toLowerCase().includes(q)) ||
        c.top_cities.some((city: string) => city.toLowerCase().includes(q))
      ) {
        const cId = c.name.toLowerCase().replace(/\s+/g, '-');
        if (!addedIds.has(cId)) {
          addedIds.add(cId);
          results.push({
            id: cId,
            title: c.name,
            subtitle: `${c.capital ? c.capital + ', ' : ''}${c.region}`,
            scope: 'INTERNATIONAL',
            visaStatus: getCountryVisaStatus(c),
          });
        }
      }
    }
  }

  return results.slice(0, 16);
}

export interface OriginLocationOption {
  id: string;
  name: string;
  detail: string;
  code?: string;
  type: 'AIRPORT' | 'CITY';
}

// Searches origin locations based on active scope:
// - INTERNATIONAL: Strictly restricted to Indian commercial departure airports with IATA codes
// - DOMESTIC: Accepts any Indian city, town, or rail hub from 4,198 cities dataset + commercial airports
export function searchOriginLocations(
  query: string,
  scope: 'DOMESTIC' | 'INTERNATIONAL' = 'INTERNATIONAL'
): OriginLocationOption[] {
  const q = query.toLowerCase().trim();
  const results: OriginLocationOption[] = [];
  const addedIds = new Set<string>();

  if (scope === 'INTERNATIONAL') {
    const matches = !q
      ? INDIAN_ORIGIN_AIRPORTS
      : INDIAN_ORIGIN_AIRPORTS.filter(
          (a) =>
            a.code.toLowerCase().includes(q) ||
            a.city.toLowerCase().includes(q) ||
            a.name.toLowerCase().includes(q) ||
            a.label.toLowerCase().includes(q)
        );

    for (const a of matches) {
      results.push({
        id: a.code,
        name: `${a.city} (${a.code})`,
        detail: a.name,
        code: a.code,
        type: 'AIRPORT',
      });
    }
    return results;
  }

  // DOMESTIC: Airports + 4,198 Cities & Rail Hubs
  const airportMatches = !q
    ? INDIAN_ORIGIN_AIRPORTS.slice(0, 8)
    : INDIAN_ORIGIN_AIRPORTS.filter(
        (a) =>
          a.code.toLowerCase().includes(q) ||
          a.city.toLowerCase().includes(q) ||
          a.name.toLowerCase().includes(q)
      );

  for (const a of airportMatches) {
    addedIds.add(a.city.toLowerCase());
    results.push({
      id: a.code,
      name: `${a.city} (${a.code})`,
      detail: `${a.name} • Departure Airport`,
      code: a.code,
      type: 'AIRPORT',
    });
  }

  if (q) {
    const places = indiaPlacesData as {
      cities: Array<{
        id: string;
        name: string;
        state_name: string;
        state_code: string;
        is_popular: boolean;
      }>;
    };

    for (const c of places.cities) {
      if (results.length >= 25) break;
      const cNameLower = c.name.toLowerCase();
      if (!addedIds.has(cNameLower) && (cNameLower.startsWith(q) || cNameLower.includes(q))) {
        addedIds.add(cNameLower);
        results.push({
          id: c.id,
          name: c.name,
          detail: `City & Rail Hub in ${c.state_name}, India`,
          type: 'CITY',
        });
      }
    }
  } else {
    const topDomesticHubs = [
      { name: 'New Delhi', detail: 'National Capital Region & Northern Hub' },
      { name: 'Mumbai', detail: 'Financial Capital & Western Hub' },
      { name: 'Bengaluru', detail: 'Karnataka Tech Capital & Southern Hub' },
      { name: 'Kolkata', detail: 'West Bengal & Eastern Hub' },
      { name: 'Chennai', detail: 'Tamil Nadu Capital & Southern Hub' },
      { name: 'Hyderabad', detail: 'Telangana Capital & Deccan Hub' },
      { name: 'Ahmedabad', detail: 'Gujarat Hub & Western Corridor' },
      { name: 'Pune', detail: 'Maharashtra Cultural & Tech Hub' },
    ];
    for (const h of topDomesticHubs) {
      if (!addedIds.has(h.name.toLowerCase())) {
        addedIds.add(h.name.toLowerCase());
        results.push({
          id: `hub-${h.name.toLowerCase()}`,
          name: h.name,
          detail: h.detail,
          type: 'CITY',
        });
      }
    }
  }

  return results.slice(0, 16);
}

// Generates dynamic, realistic transit connectors between stops
export function generateScenicTransitConnector(
  toCity: string,
  destinationInput: string,
  scope: 'DOMESTIC' | 'INTERNATIONAL' = 'INTERNATIONAL'
): { mode: string; icon: string; duration: string; title: string } {
  const destLower = (destinationInput || '').toLowerCase();

  if (destLower.includes('norway') || destLower.includes('fjord')) {
    return {
      mode: 'ferry',
      icon: 'directions_boat',
      title: `Scenic Fjord Ferry to ${toCity}`,
      duration: '~2 hrs 30 mins scenic voyage',
    };
  }

  if (destLower.includes('japan')) {
    return {
      mode: 'train',
      icon: 'train',
      title: `Shinkansen Bullet Train to ${toCity}`,
      duration: '~1 hr 45 mins',
    };
  }

  if (destLower.includes('swiss') || destLower.includes('switzerland')) {
    return {
      mode: 'train',
      icon: 'train',
      title: `Glacier / Panoramic Alpine Express to ${toCity}`,
      duration: '~2 hrs 15 mins',
    };
  }

  if (destLower.includes('kerala')) {
    return {
      mode: 'boat',
      icon: 'directions_boat',
      title: `Backwater Houseboat / Drive to ${toCity}`,
      duration: '~3 hrs scenic transit',
    };
  }

  if (destLower.includes('rajasthan')) {
    return {
      mode: 'train',
      icon: 'train',
      title: `Intercity Heritage Express to ${toCity}`,
      duration: '~3 hrs 45 mins',
    };
  }

  if (destLower.includes('ladakh') || destLower.includes('leh')) {
    return {
      mode: 'car',
      icon: 'directions_car',
      title: `High-Altitude Mountain Pass Drive to ${toCity}`,
      duration: '~4 hrs 30 mins',
    };
  }

  if (destLower.includes('goa')) {
    return {
      mode: 'car',
      icon: 'directions_car',
      title: `Coastal Highway Drive to ${toCity}`,
      duration: '~1 hr 30 mins',
    };
  }

  if (scope === 'DOMESTIC' || destLower.includes('india')) {
    return {
      mode: 'train',
      icon: 'train',
      title: `Scenic Express Train to ${toCity}`,
      duration: '~3 hrs 30 mins',
    };
  }

  return {
    mode: 'train',
    icon: 'train',
    title: `Scenic Regional Rail to ${toCity}`,
    duration: '~2 hrs 30 mins',
  };
}
