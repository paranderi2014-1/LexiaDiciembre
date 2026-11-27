export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type Database = {
  public: {
    Tables: {
      lexia_threads: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      lexia_messages: {
        Row: {
          id: string;
          thread_id: string;
          role: "user" | "assistant";
          parts: Json;
          created_at: string;
        };
        Insert: {
          id?: string;
          thread_id: string;
          role: "user" | "assistant";
          parts?: Json;
          created_at?: string;
        };
        Update: {
          id?: string;
          thread_id?: string;
          role?: "user" | "assistant";
          parts?: Json;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "lexia_messages_thread_id_fkey";
            columns: ["thread_id"];
            isOneToOne: false;
            referencedRelation: "lexia_threads";
            referencedColumns: ["id"];
          },
        ];
      };
      user_roles: {
        Row: {
          id: string;
          user_id: string;
          role: Database["public"]["Enums"]["app_role"];
        };
        Insert: {
          id?: string;
          user_id: string;
          role: Database["public"]["Enums"]["app_role"];
        };
        Update: {
          id?: string;
          user_id?: string;
          role?: Database["public"]["Enums"]["app_role"];
        };
        Relationships: [];
      };
      legal_library: {
        Row: {
          id: string;
          kind: "ley" | "fallo" | "fuente";
          title: string;
          official_url: string;
          content: string;
          reference: string;
          chamber: string;
          subject: string;
          decision_date: string | null;
          reviewed_at: string;
          published: boolean;
          created_by: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          kind: "ley" | "fallo" | "fuente";
          title: string;
          official_url: string;
          content?: string;
          reference?: string;
          chamber?: string;
          subject?: string;
          decision_date?: string | null;
          reviewed_at?: string;
          published?: boolean;
          created_by: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          kind?: "ley" | "fallo" | "fuente";
          title?: string;
          official_url?: string;
          content?: string;
          reference?: string;
          chamber?: string;
          subject?: string;
          decision_date?: string | null;
          reviewed_at?: string;
          published?: boolean;
          created_by?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      legal_cases: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          number: string;
          jurisdiction: string;
          court: string;
          district: string;
          status: string;
          risk: string;
          summary: string;
          people: string;
          official_url: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          number?: string;
          jurisdiction?: string;
          court?: string;
          district?: string;
          status?: string;
          risk?: string;
          summary?: string;
          people?: string;
          official_url?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          number?: string;
          jurisdiction?: string;
          court?: string;
          district?: string;
          status?: string;
          risk?: string;
          summary?: string;
          people?: string;
          official_url?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      case_entries: {
        Row: {
          id: string;
          case_id: string;
          kind: "actuacion" | "tarea" | "documento";
          title: string;
          body: string;
          due_date: string | null;
          done: boolean;
          file_path: string | null;
          official_url: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          case_id: string;
          kind: "actuacion" | "tarea" | "documento";
          title: string;
          body?: string;
          due_date?: string | null;
          done?: boolean;
          file_path?: string | null;
          official_url?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          case_id?: string;
          kind?: "actuacion" | "tarea" | "documento";
          title?: string;
          body?: string;
          due_date?: string | null;
          done?: boolean;
          file_path?: string | null;
          official_url?: string;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "case_entries_case_id_fkey";
            columns: ["case_id"];
            isOneToOne: false;
            referencedRelation: "legal_cases";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: Record<string, never>;
    Functions: {
      has_role: {
        Args: {
          _user_id: string;
          _role: Database["public"]["Enums"]["app_role"];
        };
        Returns: boolean;
      };
    };
    Enums: {
      app_role: "admin" | "user";
    };
    CompositeTypes: Record<string, never>;
  };
};
