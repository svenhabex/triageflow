export type CoordinatorResponseDTO = {
  availableStaff: StaffMember[];
};

export type StaffMember = {
  id: string;
  firstName: string;
  lastName: string;
  role: string;
  speciality: string;
  status: string;
};
