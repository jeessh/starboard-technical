export interface Shipment {
  id: string;
  run_id: string;
  transport_mode: "ocean_fcl" | "ocean_lcl" | "air" | null;
  incoterm: string | null;
  origin_city: string;
  origin_country: string;
  origin_address: string | null;
  dest_city: string;
  dest_country: string;
  dest_address: string | null;
  cargo_description: string | null;
  weight_kg: number | null;
  volume_cbm: number | null;
  container_type: string | null;
  container_count: number | null;
  piece_count: number | null;
  special_requirements: string[];
}

export interface ProcessedEmailSummary {
  id: string;
  filename: string;
  processed_at: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  sender_name: string;
  sender_email: string;
  sender_company: string | null;
  sender_phone: string | null;
  shipment_count: number;
}

export interface ProcessedEmail extends ProcessedEmailSummary {
  raw_email: string;
  shipments: Shipment[];
}

export interface PaginatedEmails {
  data: ProcessedEmailSummary[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ProcessEmailRequest {
  raw_email: string;
  filename: string;
}

export interface ProcessedEmailUpdate {
  filename?: string;
  sender_name?: string;
  sender_email?: string;
  sender_company?: string | null;
  sender_phone?: string | null;
}

export type ShipmentUpdate = Partial<Omit<Shipment, "id" | "run_id">>;
