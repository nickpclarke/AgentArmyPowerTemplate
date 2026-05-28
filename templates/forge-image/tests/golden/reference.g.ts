// @generated — emitted by agentarmy-forge
//   forge.version: 0.1.0
//   model.version: 1.0.0
//   source.uri:    file:///work/reference.model.yaml
//   DO NOT EDIT. Re-run forge against the source ontology to regenerate.

import { z } from 'zod';

export interface User {
  id: string;
  handle: string;
  createdAt: string;
  documents: Document[];
}

export interface Document {
  id: string;
  title: string;
  body: string | null;
  wordCount: number;
  createdAt: string;
  author: User;
}

export const UserSchema = z.object({
  id: z.string().uuid(),
  handle: z.string(),
  createdAt: z.string().datetime(),
});

export const DocumentSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  body: z.string().nullable(),
  wordCount: z.number().int(),
  createdAt: z.string().datetime(),
});
