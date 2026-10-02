export type Daypart = 'MORNING' | 'AFTERNOON' | 'EVENING';

export interface PointOfInterest {
  name: string;
  category: string;
  city: string;
  country?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  description?: string;
  estimated_duration_minutes?: number;
  estimated_cost_inr: number;
  is_must_visit?: boolean;
  maps_url?: string;
  provider?: string;
}

export interface ActivitySlot {
  daypart: Daypart;
  poi: PointOfInterest;
  notes?: string;
  is_weather_substituted?: boolean;
  substituted_for?: string;
  weather_note?: string;
}

export interface DayMeal {
  meal_type: 'BREAKFAST' | 'LUNCH' | 'DINNER';
  name: string;
  cuisine: string;
  estimated_cost_inr: number;
  notes?: string;
  restaurant_name?: string;
}

export interface DayPlan {
  day_number: number;
  date: string;
  city: string;
  theme: string;
  activities: ActivitySlot[];
  meals: DayMeal[];
  weather_forecast?: {
    condition: string;
    temp_celsius: number;
    temp_high_celsius?: number;
    temp_low_celsius?: number;
    precipitation_chance?: number;
    advisory?: string;
    icon?: string;
  };
  stay?: {
    name: string;
    type: string;
    neighborhood: string;
    cost_inr: number;
    confirmed?: boolean;
    check_in?: string;
    amenities?: string[];
  };
  metrics?: {
    active_hours: number;
    rest_hours: number;
    walking_steps: number;
    walking_km: number;
    pacing_label: string;
  };
  featured_experience?: {
    title: string;
    subtitle: string;
    time_window: string;
    duration: string;
    image_url: string;
    image_alt?: string;
    tags: string[];
    why_included: string;
    curator_tips: string[];
    transit_connection?: string;
  };
  hourly_atmosphere?: {
    time: string;
    temp: string;
    condition: string;
    precipitation: string;
    icon: string;
  }[];
  day_budget?: {
    activities_inr: number;
    meals_inr: number;
    transit_inr: number;
    stays_inr: number;
    total_inr: number;
  };
  next_day_teaser?: {
    day_number: number;
    theme: string;
    city: string;
  };
}

export interface TransportMilestone {
  time: string;
  label: string;
  location: string;
  description: string;
  icon?: string;
  status?: 'completed' | 'active' | 'upcoming';
}

export interface IntermediateStation {
  station: string;
  time: string;
  platform?: string;
  notes?: string;
}

export interface TransportLeg {
  id?: string;
  origin: string;
  destination: string;
  mode: string; // e.g. "FLIGHT", "SHINKANSEN", "TRAIN", "TAXI"
  operator?: string;
  duration: string;
  cost_inr: number;
  departure_time?: string;
  arrival_time?: string;
  distance_km?: number;
  notes?: string;
  service_name?: string;
  carrier?: string;
  equipment?: string;
  seat_reservation?: string;
  luggage_policy?: string;
  pass_coverage?: string;
  travel_date?: string;
  fare_breakdown?: {
    base_fare_inr: number;
    seat_reservation_inr: number;
    currency_local?: string;
    total_local?: string;
    status?: string;
  };
  milestones?: TransportMilestone[];
  intermediate_stops?: IntermediateStation[];
}

export interface NeighborhoodWaypoint {
  id: string;
  name: string;
  native_name?: string;
  description: string;
  recommended_time: string;
  duration: string;
  highlights: string[];
  image_url: string;
}

export interface DestinationDetail {
  name: string;
  native_script: string;
  region: string;
  country: string;
  stop_number: number;
  total_stops: number;
  nights: number;
  stay_dates: string;
  hero_image: string;
  editorial_intro: string;
  sanctuary_lodging_callout: string;
  snapshot: {
    recommended_stay: string;
    seasonal_context: string;
    weather_context: string;
    currency_fx: string;
    language: string;
    timezone: string;
  };
  curator_selection: {
    quote: string;
    tags: string[];
    active_discovery_hours: number;
    active_ratio_percent: number;
    leisure_ratio_percent: number;
  };
  neighborhoods: NeighborhoodWaypoint[];
  mobility_guide: {
    arrival_overview: string;
    local_transit: string;
    walking_notes: string;
  };
  next_stop?: {
    destination: string;
    transport_mode: string;
    service_name: string;
    duration: string;
    leg_id?: string;
  };
}

export interface HotelStay {
  id?: string;
  hotel_name: string;
  city: string;
  check_in: string;
  check_out: string;
  nights: number;
  cost_inr: number;
  style?: string;
  neighborhood?: string;
  confirmed?: boolean;
}

export interface BudgetBreakdown {
  total_with_contingency_inr: number;
  subtotal_inr: number;
  contingency_inr: number;
  stays_inr: number;
  transport_inr: number;
  activities_inr: number;
  food_inr: number;
  contingency_percentage: number;
  variance: {
    user_budget_inr: number;
    variance_inr: number;
    variance_percentage: number;
    status: 'FAVORABLE' | 'UNFAVORABLE' | 'EXACT' | string;
  };
}

export interface HighlightMoment {
  day: number;
  city: string;
  title: string;
  description: string;
  image_url: string;
  image_alt?: string;
}

export interface MicroclimateItem {
  city: string;
  temp: string;
  condition: string;
  icon: string;
  note: string;
}

export interface FinalItinerary {
  trip_id: string;
  title: string;
  summary: string;
  curator_note?: string;
  cover_image?: {
    url: string;
    alt: string;
    waypoint_title: string;
    stay_highlight: string;
    seasonal_badge: string;
  };
  pace_rhythm_index?: {
    cultural_immersiveness: number;
    transit_leisure_margin: number;
    vetted_by?: string;
  };
  trip_context: {
    origin: string;
    destinations: string[];
    start_date: string;
    end_date: string;
    duration_days: number;
    budget_inr: number;
    num_travelers: number;
    travel_style: string;
    pace: string;
    scope?: 'DOMESTIC' | 'INTERNATIONAL';
  };
  logistics_plan: {
    transport_legs: TransportLeg[];
    hotel_stays: HotelStay[];
    total_transport_cost_inr: number;
    total_accommodation_cost_inr: number;
  };
  experience_plan: {
    total_days: number;
    days: DayPlan[];
    total_activity_cost_inr: number;
    total_food_cost_inr: number;
    highlights?: HighlightMoment[];
  };
  budget_breakdown: BudgetBreakdown;
  visa_verdict?: {
    is_domestic_bypass: boolean;
    status?: string;
    notes?: string;
  };
  weather_context?: MicroclimateItem[];
  plan_status: string;
  created_at: string;
}

export interface PlanningEvent {
  event: string;
  stage: string;
  message: string;
  data?: Record<string, any>;
  timestamp?: string;
}

export interface PlanRunState {
  status: 'idle' | 'streaming' | 'completed' | 'error';
  currentStage: string;
  progressPercent: number;
  elapsedSeconds: number;
  events: PlanningEvent[];
  error?: string;
}
