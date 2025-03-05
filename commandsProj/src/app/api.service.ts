import { Injectable } from '@angular/core';
import axios from 'axios';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000';

  async uploadImage(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${this.backendUrl}/process/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  }
}
