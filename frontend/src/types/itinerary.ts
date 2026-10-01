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
    advisory?: string;
    icon?: string;
  };
  stay?: {
    name: string;
    type: string;
    neighborhood: string;
    cost_inr: number;
    confirmed?: boolean;
  };
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
