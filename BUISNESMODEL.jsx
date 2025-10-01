import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, AreaChart, Area } from 'recharts';

const NormScoutBusinessPlan = () => {
  const [selectedPrice, setSelectedPrice] = useState(12);
  const [selectedPreSeed, setSelectedPreSeed] = useState('none');
  const [selectedSeriesA, setSelectedSeriesA] = useState('none');
  const [selectedLifetime, setSelectedLifetime] = useState('8q');
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobile, setIsMobile] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const quarters = ['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026', 'Q1 2027', 'Q2 2027', 'Q3 2027', 'Q4 2027', 'Q1 2028', 'Q2 2028', 'Q3 2028', 'Q4 2028'];
  
  const pricePoints = [8, 12, 18, 24];
  
  const customerLifetimes = {
    '1q': { quarters: 1, label: '3 months', monthlyChurn: 0.333 },
    '4q': { quarters: 4, label: '1 year', monthlyChurn: 0.083 },
    '8q': { quarters: 8, label: '2 years', monthlyChurn: 0.042 },
    'infinite': { quarters: 999, label: 'No churn', monthlyChurn: 0 }
  };
  
  const preSeedFunding = {
    none: 0,
    pessimistic: 10000,
    normal: 25000,
    optimistic: 50000
  };
  
  const seriesAFunding = {
    none: 0,
    pessimistic: 300000,
    normal: 700000,
    optimistic: 1500000
  };
  
  const baseScenarios = {
    pessimistic: [50, 120, 150, 300, 450, 550, 650, 750, 850, 950, 1050, 1150],
    normal: [150, 310, 575, 900, 1200, 1550, 1900, 2300, 2700, 3200, 3700, 4300],
    optimistic: [250, 500, 1000, 2000, 3500, 5000, 6500, 8000, 9500, 11000, 12500, 14000]
  };
  
  const priceMultipliers = {
    8: 1.8,
    12: 1.4,
    18: 1.0,
    24: 0.7
  };
  
  const baseCAC = {
    pessimistic: [35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25.5, 25],
    normal: [25, 23.5, 22, 20.5, 19, 17.5, 16, 14.5, 13, 11.5, 10.5, 10],
    optimistic: [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5.5, 5]
  };
  
  const cacMultipliers = {
    8: 0.7,
    12: 0.85,
    18: 1.0,
    24: 1.3
  };
  
  const opCosts = { pessimistic: 4.5, normal: 3.0, optimistic: 2.0 };
  
  const getAdSpendPerQuarter = (quarterIdx) => {
    let adSpend = 0;
    if (quarterIdx < 4) {
      adSpend += preSeedFunding[selectedPreSeed] / 4;
    }
    if (quarterIdx >= 4) {
      adSpend += seriesAFunding[selectedSeriesA] / 8;
    }
    return adSpend;
  };
  
  const calculateUserBoost = (baseUsers, quarterIdx, scenario) => {
    const adSpend = getAdSpendPerQuarter(quarterIdx);
    if (adSpend === 0) return baseUsers;
    
    const effectiveness = {
      pessimistic: 0.005,  // Reduced from 0.01
      normal: 0.01,        // Reduced from 0.02
      optimistic: 0.015    // Reduced from 0.03
    };
    
    // More gradual multipliers
    const earlyUserMultiplier = quarterIdx < 4 ? 1.2 : 1.0;  // Reduced from 1.5
    const networkEffect = Math.pow(1.05, quarterIdx);  // Reduced from 1.1
    const boost = Math.round(adSpend * effectiveness[scenario] * earlyUserMultiplier * networkEffect);
    
    let preSeedLegacyBoost = 0;
    if (quarterIdx >= 4 && preSeedFunding[selectedPreSeed] > 0) {
      const momentumMultiplier = {
        pessimistic: 0.1,   // Reduced from 0.2
        normal: 0.15,       // Reduced from 0.3
        optimistic: 0.2     // Reduced from 0.4
      };
      preSeedLegacyBoost = Math.round(
        preSeedFunding[selectedPreSeed] * 0.0005 * momentumMultiplier[selectedPreSeed] * (quarterIdx - 3)  // Reduced from 0.001
      );
    }
    
    return baseUsers + boost + preSeedLegacyBoost;
  };
  
  const calculateImprovedCAC = (baseCac, quarterIdx, scenario) => {
    const adSpend = getAdSpendPerQuarter(quarterIdx);
    const preSeedImpact = preSeedFunding[selectedPreSeed];
    
    let cacReduction = 1.0;
    
    if (preSeedImpact > 0) {
      const brandAwareness = Math.min(0.4, (preSeedImpact / 50000) * 0.4);
      cacReduction *= (1 - brandAwareness);
      const timeDecay = Math.exp(-quarterIdx * 0.05);
      cacReduction *= (1 - (1 - timeDecay) * 0.2);
    }
    
    if (adSpend > 0) {
      const currentImprovement = Math.min(0.3, (adSpend / 100000) * 0.3);
      cacReduction *= (1 - currentImprovement);
    }
    
    return baseCac * cacReduction;
  };
  
  const scaleAndBoostUsers = (baseUsers, price, scenario) => {
    return baseUsers.map((u, idx) => {
      const scaled = Math.round(u * priceMultipliers[price]);
      const boosted = calculateUserBoost(scaled, idx, scenario);
      
      if (selectedPreSeed !== 'none' && idx > 0) {
        const growthMultiplier = {
          pessimistic: 1.02,
          normal: 1.03,
          optimistic: 1.04
        };
        return Math.round(boosted * Math.pow(growthMultiplier[selectedPreSeed], idx));
      }
      
      return boosted;
    });
  };
  
  const scaleAndImproveCAC = (baseCac, price, scenario) => {
    return baseCac.map((c, idx) => {
      const scaled = c * cacMultipliers[price];
      return parseFloat(calculateImprovedCAC(scaled, idx, scenario).toFixed(2));
    });
  };
  
  const calculateProfitabilityWithChurn = (targetUsers, price, cac, opCost, scenario) => {
    let bankBalance = 0;
    const results = [];
    const lifetime = customerLifetimes[selectedLifetime];
    let cohorts = [];
    
    for (let idx = 0; idx < targetUsers.length; idx++) {
      if (idx === 0) bankBalance += preSeedFunding[selectedPreSeed];
      if (idx === 4) bankBalance += seriesAFunding[selectedSeriesA];
      
      const previousActiveUsers = idx === 0 ? 0 : 
        cohorts.reduce((sum, c) => sum + c.currentUsers, 0);
      
      if (idx > 0) {
        cohorts = cohorts.map(cohort => {
          const monthsSinceAcquisition = (idx - cohort.quarter) * 3;
          let retention = 1;
          
          if (lifetime.monthlyChurn > 0 && monthsSinceAcquisition > 0) {
            retention = Math.pow(1 - lifetime.monthlyChurn, monthsSinceAcquisition);
            // Removed the artificial halving after expected lifetime - the exponential decay is enough
          }
          
          return {
            ...cohort,
            currentUsers: Math.round(cohort.initialUsers * retention)
          };
        });
      }
      
      const currentActiveFromCohorts = cohorts.reduce((sum, c) => sum + c.currentUsers, 0);
      const churnedThisQ = idx === 0 ? 0 : 
        Math.max(0, previousActiveUsers - currentActiveFromCohorts);
      
      // FIXED: Only acquire new users based on target growth, NOT replacing all churn
      // This makes churn actually impact the active user count
      const targetGrowth = idx === 0 ? targetUsers[idx] : 
        targetUsers[idx] - targetUsers[idx - 1];
      
      // Option 1: Acquire exactly the target growth (churn reduces total active)
      const newUsersNeeded = Math.max(0, targetGrowth);
      
      // Option 2 (commented): Try to maintain trajectory but with some churn impact
      // const replacementFactor = 0.5; // Only replace 50% of churned users
      // const newUsersNeeded = Math.max(0, targetGrowth + (churnedThisQ * replacementFactor));
      
      if (newUsersNeeded > 0) {
        cohorts.push({
          quarter: idx,
          initialUsers: newUsersNeeded,
          currentUsers: newUsersNeeded
        });
      }
      
      const activeUsers = cohorts.reduce((sum, c) => sum + c.currentUsers, 0);
      const organicAcquisitionCost = newUsersNeeded * cac[idx];
      const adSpend = getAdSpendPerQuarter(idx);
      const totalAcquisitionCost = organicAcquisitionCost + adSpend;
      const quarterlyOperationalCost = activeUsers * opCost * 3;
      const quarterlyRevenue = activeUsers * price * 3;
      const quarterlyProfit = quarterlyRevenue - quarterlyOperationalCost - totalAcquisitionCost;
      bankBalance += quarterlyProfit;
      
      const ltv = lifetime.monthlyChurn > 0 ? 
        price / lifetime.monthlyChurn : price * 36;
      
      results.push({
        quarter: quarters[idx],
        newUsers: newUsersNeeded,
        activeUsers: activeUsers,
        churnedUsers: churnedThisQ,
        revenue: quarterlyRevenue,
        operationalCost: quarterlyOperationalCost,
        acquisitionCost: organicAcquisitionCost,
        adSpend: adSpend,
        profit: quarterlyProfit,
        bankBalance: bankBalance,
        cac: cac[idx],
        ltv: ltv,
        ltvCacRatio: ltv / cac[idx],
        cohortCount: cohorts.length,
        replacementRate: newUsersNeeded > 0 ? (churnedThisQ / newUsersNeeded * 100) : 0
      });
    }
    return results;
  };
  
  const pessimisticUsers = scaleAndBoostUsers(baseScenarios.pessimistic, selectedPrice, 'pessimistic');
  const normalUsers = scaleAndBoostUsers(baseScenarios.normal, selectedPrice, 'normal');
  const optimisticUsers = scaleAndBoostUsers(baseScenarios.optimistic, selectedPrice, 'optimistic');
  
  const pessimisticCAC = scaleAndImproveCAC(baseCAC.pessimistic, selectedPrice, 'pessimistic');
  const normalCAC = scaleAndImproveCAC(baseCAC.normal, selectedPrice, 'normal');
  const optimisticCAC = scaleAndImproveCAC(baseCAC.optimistic, selectedPrice, 'optimistic');
  
  const pessimisticData = calculateProfitabilityWithChurn(pessimisticUsers, selectedPrice, pessimisticCAC, opCosts.pessimistic, 'pessimistic');
  const normalData = calculateProfitabilityWithChurn(normalUsers, selectedPrice, normalCAC, opCosts.normal, 'normal');
  const optimisticData = calculateProfitabilityWithChurn(optimisticUsers, selectedPrice, optimisticCAC, opCosts.optimistic, 'optimistic');
  
  // This should use the actual active users from the profitability calculation
  // which properly accounts for churn
  const userGrowthData = quarters.map((q, idx) => ({
    quarter: q,
    pessimistic: pessimisticData[idx].activeUsers,
    normal: normalData[idx].activeUsers,
    optimistic: optimisticData[idx].activeUsers
  }));
  
  const revenueData = quarters.map((q, idx) => ({
    quarter: q,
    pessimistic: pessimisticData[idx].revenue,
    normal: normalData[idx].revenue,
    optimistic: optimisticData[idx].revenue
  }));
  
  const mrrData = quarters.map((q, idx) => ({
    quarter: q,
    pessimistic: (pessimisticData[idx].revenue / 3),  // Convert quarterly to monthly
    normal: (normalData[idx].revenue / 3),
    optimistic: (optimisticData[idx].revenue / 3)
  }));
  
  const bankBalanceData = quarters.map((q, idx) => ({
    quarter: q,
    pessimistic: pessimisticData[idx].bankBalance,
    normal: normalData[idx].bankBalance,
    optimistic: optimisticData[idx].bankBalance
  }));
  
  const adSpendData = quarters.map((q, idx) => ({
    quarter: q,
    preSeed: idx < 4 ? preSeedFunding[selectedPreSeed] / 4 : 0,
    seriesA: idx >= 4 ? seriesAFunding[selectedSeriesA] / 8 : 0,
    total: getAdSpendPerQuarter(idx)
  }));
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };
  
  const formatCompactCurrency = (value) => {
    if (value >= 1000000) return `$${(value/1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value/1000).toFixed(0)}k`;
    return `$${value}`;
  };
  
  const calculateTotals = (data) => {
    const totalRevenue = data.reduce((sum, q) => sum + q.revenue, 0);
    const totalCosts = data.reduce((sum, q) => sum + q.operationalCost + q.acquisitionCost + q.adSpend, 0);
    const totalNewUsers = data.reduce((sum, q) => sum + q.newUsers, 0);
    const totalChurned = data.reduce((sum, q) => sum + q.churnedUsers, 0);
    const finalBalance = data[data.length - 1].bankBalance;
    const totalFunding = preSeedFunding[selectedPreSeed] + seriesAFunding[selectedSeriesA];
    const roi = totalFunding > 0 ? ((finalBalance - totalFunding) / totalFunding * 100) : 0;
    const finalUsers = data[data.length - 1].activeUsers;
    const avgLtvCac = data.reduce((sum, q) => sum + q.ltvCacRatio, 0) / data.length;
    const netUserGrowth = totalNewUsers - totalChurned;
    
    return { 
      totalRevenue, 
      totalCosts, 
      finalBalance, 
      totalFunding, 
      roi, 
      finalUsers,
      totalNewUsers,
      totalChurned,
      netUserGrowth,
      avgLtvCac,
      churnRate: customerLifetimes[selectedLifetime].monthlyChurn * 100
    };
  };
  
  const pessimisticTotals = calculateTotals(pessimisticData);
  const normalTotals = calculateTotals(normalData);
  const optimisticTotals = calculateTotals(optimisticData);
  
  const downloadExcel = () => {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
    script.onload = () => generateExcel();
    document.head.appendChild(script);
  };

  const generateExcel = () => {
    const XLSX = window.XLSX;
    const wb = XLSX.utils.book_new();
    
    const separatorLine = '============================================================';
    
    const legendData = [
      ['NORMSCOUT INVESTMENT MODEL - COMPREHENSIVE EXPORT'],
      [separatorLine],
      ['Generated: ' + new Date().toLocaleString()],
      ['Model Version: 2.0'],
      [],
      ['CURRENT CONFIGURATION'],
      [separatorLine],
      ['Parameter', 'Selected Value', 'Description'],
      ['Pre-seed Funding', formatCurrency(preSeedFunding[selectedPreSeed]), 'Early stage funding for initial growth and market validation'],
      ['Series A Funding', formatCurrency(seriesAFunding[selectedSeriesA]), 'Growth capital for scaling operations and customer acquisition'],
      ['Monthly Subscription', '$' + selectedPrice, 'Recurring monthly revenue per active customer'],
      ['Customer Lifetime', customerLifetimes[selectedLifetime].label, `Average customer retention period (${(customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1)}% monthly churn)`],
      [],
      ['KEY METRICS GLOSSARY'],
      [separatorLine],
      ['Metric', 'Definition', 'Formula/Calculation'],
      ['Active Users', 'Total paying customers at end of quarter', 'Previous Active + New Users - Churned Users'],
      ['New Users', 'Customers acquired during the quarter', 'Target Growth + Replacement for Churned'],
      ['Churned Users', 'Customers lost during the quarter', 'Based on monthly churn rate compounded over 3 months'],
      ['Revenue', 'Total quarterly subscription revenue', 'Active Users × Monthly Price × 3 months'],
      ['CAC', 'Customer Acquisition Cost', 'Total acquisition spend / New users acquired'],
      ['LTV', 'Customer Lifetime Value', 'Monthly Price / Monthly Churn Rate (or Price × 36 for no churn)'],
      ['LTV/CAC Ratio', 'Unit economics indicator', 'LTV divided by CAC (>3 is excellent, >1 is profitable)'],
      ['Operational Cost', 'Cost to serve active customers', 'Active Users × Op Cost per User × 3 months'],
      ['Ad Spend', 'Marketing investment from funding', 'Allocated portion of Pre-seed/Series A funding'],
      ['Bank Balance', 'Cumulative cash position', 'Previous Balance + Revenue - All Costs'],
      ['ROI', 'Return on Investment', '(Final Balance - Total Funding) / Total Funding × 100%'],
      [],
      ['SCENARIO DEFINITIONS'],
      [separatorLine],
      ['Scenario', 'Description', 'Key Assumptions'],
      ['Pessimistic', 'Conservative growth case', 'Slow user growth, high CAC, higher operational costs'],
      ['Normal', 'Base case projection', 'Moderate growth, improving CAC over time, standard ops'],
      ['Optimistic', 'Aggressive growth case', 'Rapid user acquisition, efficient CAC, lean operations'],
      [],
      ['FUNDING IMPACT MECHANICS'],
      [separatorLine],
      ['Funding Type', 'Timing', 'Primary Use', 'Expected Impact'],
      ['Pre-seed', 'Q1-Q4 2026', 'Early customer acquisition', 'Establishes initial user base and brand awareness'],
      ['Series A', 'Q1 2027+', 'Scale growth operations', 'Accelerates user acquisition and reduces CAC through efficiency'],
      [],
      ['EXCEL SHEETS GUIDE'],
      [separatorLine],
      ['Sheet Name', 'Contents'],
      ['Legend & Overview', 'This page - Configuration, definitions, and guide'],
      ['Executive Summary', 'High-level results and key metrics comparison'],
      ['Normal Scenario', 'Detailed quarterly projections for base case'],
      ['Pessimistic Scenario', 'Detailed quarterly projections for conservative case'],
      ['Optimistic Scenario', 'Detailed quarterly projections for aggressive case'],
      ['User Metrics', 'User acquisition, retention, and churn analysis'],
      ['Financial Metrics', 'Revenue, costs, and profitability breakdown'],
      ['Cohort Analysis', 'Customer cohort retention patterns'],
      ['Sensitivity Analysis', 'Impact of key variables on outcomes']
    ];
    
    const legendSheet = XLSX.utils.aoa_to_sheet(legendData);
    legendSheet['!cols'] = [
      { wch: 25 }, { wch: 30 }, { wch: 50 }, { wch: 40 }
    ];
    XLSX.utils.book_append_sheet(wb, legendSheet, 'Legend & Overview');
    
    const summaryData = [
      ['EXECUTIVE SUMMARY'],
      [separatorLine],
      [],
      ['Key Configuration'],
      ['Total Funding', formatCurrency(preSeedFunding[selectedPreSeed] + seriesAFunding[selectedSeriesA])],
      ['Pre-seed', formatCurrency(preSeedFunding[selectedPreSeed])],
      ['Series A', formatCurrency(seriesAFunding[selectedSeriesA])],
      ['Monthly Price', '$' + selectedPrice],
      ['Customer Lifetime', customerLifetimes[selectedLifetime].label],
      ['Monthly Churn Rate', (customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1) + '%'],
      [],
      ['Final Results (Q4 2028)', 'Pessimistic', 'Normal', 'Optimistic'],
      ['Active Users', pessimisticTotals.finalUsers, normalTotals.finalUsers, optimisticTotals.finalUsers],
      ['Total Users Acquired', pessimisticTotals.totalNewUsers, normalTotals.totalNewUsers, optimisticTotals.totalNewUsers],
      ['Total Users Churned', pessimisticTotals.totalChurned, normalTotals.totalChurned, optimisticTotals.totalChurned],
      ['Net User Growth', pessimisticTotals.netUserGrowth, normalTotals.netUserGrowth, optimisticTotals.netUserGrowth],
      ['Total Revenue', formatCurrency(pessimisticTotals.totalRevenue), formatCurrency(normalTotals.totalRevenue), formatCurrency(optimisticTotals.totalRevenue)],
      ['Total Costs', formatCurrency(pessimisticTotals.totalCosts), formatCurrency(normalTotals.totalCosts), formatCurrency(optimisticTotals.totalCosts)],
      ['Final Bank Balance', formatCurrency(pessimisticTotals.finalBalance), formatCurrency(normalTotals.finalBalance), formatCurrency(optimisticTotals.finalBalance)],
      ['ROI %', pessimisticTotals.roi.toFixed(1) + '%', normalTotals.roi.toFixed(1) + '%', optimisticTotals.roi.toFixed(1) + '%'],
      ['Avg LTV/CAC Ratio', pessimisticTotals.avgLtvCac.toFixed(2), normalTotals.avgLtvCac.toFixed(2), optimisticTotals.avgLtvCac.toFixed(2)],
      [],
      ['Profitability Timeline'],
      ['Break-even Quarter', 
        pessimisticData.find(d => d.bankBalance > 0)?.quarter || 'Not reached',
        normalData.find(d => d.bankBalance > 0)?.quarter || 'Not reached',
        optimisticData.find(d => d.bankBalance > 0)?.quarter || 'Not reached'
      ],
      ['Quarters to Positive Cash', 
        pessimisticData.findIndex(d => d.bankBalance > 0) + 1 || 'N/A',
        normalData.findIndex(d => d.bankBalance > 0) + 1 || 'N/A',
        optimisticData.findIndex(d => d.bankBalance > 0) + 1 || 'N/A'
      ]
    ];
    
    const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);
    summarySheet['!cols'] = [{ wch: 30 }, { wch: 20 }, { wch: 20 }, { wch: 20 }];
    XLSX.utils.book_append_sheet(wb, summarySheet, 'Executive Summary');
    
    const createScenarioSheet = (data, scenario) => {
      const headers = [
        ['Quarter', 'New Users', 'Active Users', 'Churned Users', 'Replacement Rate %', 
         'Revenue', 'Operational Cost', 'Acquisition Cost', 'Ad Spend', 'Total Cost',
         'Quarterly Profit', 'Bank Balance', 'CAC', 'LTV', 'LTV/CAC Ratio', 'Cohort Count']
      ];
      
      const rows = data.map(row => [
        row.quarter,
        row.newUsers,
        row.activeUsers,
        row.churnedUsers,
        row.replacementRate.toFixed(1),
        row.revenue,
        row.operationalCost,
        row.acquisitionCost,
        row.adSpend,
        row.operationalCost + row.acquisitionCost + row.adSpend,
        row.profit,
        row.bankBalance,
        row.cac.toFixed(2),
        row.ltv.toFixed(2),
        row.ltvCacRatio.toFixed(2),
        row.cohortCount
      ]);
      
      return XLSX.utils.aoa_to_sheet([...headers, ...rows]);
    };
    
    const normalSheet = createScenarioSheet(normalData, 'Normal');
    normalSheet['!cols'] = Array(16).fill({ wch: 15 });
    XLSX.utils.book_append_sheet(wb, normalSheet, 'Normal Scenario');
    
    const pessimisticSheet = createScenarioSheet(pessimisticData, 'Pessimistic');
    pessimisticSheet['!cols'] = Array(16).fill({ wch: 15 });
    XLSX.utils.book_append_sheet(wb, pessimisticSheet, 'Pessimistic Scenario');
    
    const optimisticSheet = createScenarioSheet(optimisticData, 'Optimistic');
    optimisticSheet['!cols'] = Array(16).fill({ wch: 15 });
    XLSX.utils.book_append_sheet(wb, optimisticSheet, 'Optimistic Scenario');
    
    const userMetricsData = [
      ['Quarter', 'Pessimistic Users', 'Normal Users', 'Optimistic Users',
       'Pessimistic New', 'Normal New', 'Optimistic New',
       'Pessimistic Churned', 'Normal Churned', 'Optimistic Churned']
    ];
    
    quarters.forEach((q, idx) => {
      userMetricsData.push([
        q,
        pessimisticData[idx].activeUsers,
        normalData[idx].activeUsers,
        optimisticData[idx].activeUsers,
        pessimisticData[idx].newUsers,
        normalData[idx].newUsers,
        optimisticData[idx].newUsers,
        pessimisticData[idx].churnedUsers,
        normalData[idx].churnedUsers,
        optimisticData[idx].churnedUsers
      ]);
    });
    
    const userSheet = XLSX.utils.aoa_to_sheet(userMetricsData);
    userSheet['!cols'] = Array(10).fill({ wch: 18 });
    XLSX.utils.book_append_sheet(wb, userSheet, 'User Metrics');
    
    const financialData = [
      ['Quarter', 'Pessimistic Revenue', 'Normal Revenue', 'Optimistic Revenue',
       'Pessimistic Costs', 'Normal Costs', 'Optimistic Costs',
       'Pessimistic Balance', 'Normal Balance', 'Optimistic Balance']
    ];
    
    quarters.forEach((q, idx) => {
      financialData.push([
        q,
        pessimisticData[idx].revenue,
        normalData[idx].revenue,
        optimisticData[idx].revenue,
        pessimisticData[idx].operationalCost + pessimisticData[idx].acquisitionCost + pessimisticData[idx].adSpend,
        normalData[idx].operationalCost + normalData[idx].acquisitionCost + normalData[idx].adSpend,
        optimisticData[idx].operationalCost + optimisticData[idx].acquisitionCost + optimisticData[idx].adSpend,
        pessimisticData[idx].bankBalance,
        normalData[idx].bankBalance,
        optimisticData[idx].bankBalance
      ]);
    });
    
    const financialSheet = XLSX.utils.aoa_to_sheet(financialData);
    financialSheet['!cols'] = Array(10).fill({ wch: 20 });
    XLSX.utils.book_append_sheet(wb, financialSheet, 'Financial Metrics');
    
    const cohortData = [
      ['COHORT RETENTION ANALYSIS'],
      ['Customer Lifetime: ' + customerLifetimes[selectedLifetime].label],
      ['Monthly Churn Rate: ' + (customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1) + '%'],
      [],
      ['Months Since Acquisition', 'Retention %', 'Users Remaining (from 100)']
    ];
    
    for (let month = 0; month <= 36; month += 3) {
      const retention = customerLifetimes[selectedLifetime].monthlyChurn > 0 
        ? Math.pow(1 - customerLifetimes[selectedLifetime].monthlyChurn, month) 
        : 1;
      cohortData.push([
        month,
        (retention * 100).toFixed(1) + '%',
        Math.round(retention * 100)
      ]);
    }
    
    const cohortSheet = XLSX.utils.aoa_to_sheet(cohortData);
    cohortSheet['!cols'] = [{ wch: 25 }, { wch: 15 }, { wch: 25 }];
    XLSX.utils.book_append_sheet(wb, cohortSheet, 'Cohort Analysis');
    
    const sensitivityData = [
      ['SENSITIVITY ANALYSIS'],
      ['How key variables impact the Normal scenario outcome'],
      [],
      ['Variable', 'Current Value', '-20%', 'Base', '+20%', 'Impact'],
      ['Monthly Price', '$' + selectedPrice, 
        'Balance: ' + formatCompactCurrency(normalTotals.finalBalance * 0.8),
        'Balance: ' + formatCompactCurrency(normalTotals.finalBalance),
        'Balance: ' + formatCompactCurrency(normalTotals.finalBalance * 1.2),
        'High Impact'],
      ['Monthly Churn', (customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1) + '%',
        'Better retention',
        'Current',
        'Worse retention',
        'High Impact'],
      ['CAC Efficiency', 'Variable',
        'Lower costs',
        'Current',
        'Higher costs',
        'Medium Impact'],
      ['Operational Costs', '$' + opCosts.normal + '/user/month',
        'Lean operations',
        'Current',
        'Higher costs',
        'Medium Impact']
    ];
    
    const sensitivitySheet = XLSX.utils.aoa_to_sheet(sensitivityData);
    sensitivitySheet['!cols'] = [{ wch: 20 }, { wch: 15 }, { wch: 20 }, { wch: 20 }, { wch: 20 }, { wch: 15 }];
    XLSX.utils.book_append_sheet(wb, sensitivitySheet, 'Sensitivity Analysis');
    
    XLSX.writeFile(wb, `NormScout_Model_${new Date().toISOString().slice(0,10)}.xlsx`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
      <div className="bg-black border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">
                <span className="text-blue-500">NormScout</span> Model
              </h1>
              <p className="text-zinc-400 mt-1 text-sm sm:text-base">Investment Projections 2026-2028</p>
            </div>
            <button
              onClick={downloadExcel}
              className="bg-green-600 hover:bg-green-700 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition-all flex items-center gap-2 text-sm sm:text-base"
            >
              <span>📊</span> Export Excel
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        {isMobile && (
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="w-full mb-4 bg-zinc-800 p-4 rounded-lg flex items-center justify-between"
          >
            <span className="font-semibold">Configuration</span>
            <span className="text-2xl">{showMobileMenu ? '−' : '+'}</span>
          </button>
        )}

        <div className={`bg-zinc-900 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8 border border-zinc-800 ${isMobile && !showMobileMenu ? 'hidden' : ''}`}>
          <h2 className="text-lg sm:text-xl font-semibold mb-4 text-zinc-300">Investment Configuration</h2>
          
          <div className={`grid ${isMobile ? 'grid-cols-1 gap-4' : 'grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6'}`}>
            <div>
              <label className="block text-xs sm:text-sm font-medium text-zinc-400 mb-2 sm:mb-3">
                🌱 Pre-seed (Q1 2026)
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-2 gap-1 sm:gap-2">
                {Object.entries(preSeedFunding).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedPreSeed(key)}
                    className={`px-2 sm:px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      selectedPreSeed === key
                        ? 'bg-purple-600 text-white shadow-lg'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                    }`}
                  >
                    {key === 'none' ? 'None' : `$${(value/1000).toFixed(0)}k`}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-zinc-400 mb-2 sm:mb-3">
                🚀 Series A
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-2 gap-1 sm:gap-2">
                {Object.entries(seriesAFunding).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedSeriesA(key)}
                    className={`px-2 sm:px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      selectedSeriesA === key
                        ? 'bg-green-600 text-white shadow-lg'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                    }`}
                  >
                    {key === 'none' ? 'None' : formatCompactCurrency(value)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-zinc-400 mb-2 sm:mb-3">
                ⏱️ Lifetime
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-2 gap-1 sm:gap-2">
                {Object.entries(customerLifetimes).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedLifetime(key)}
                    className={`px-2 sm:px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      selectedLifetime === key
                        ? 'bg-orange-600 text-white shadow-lg'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                    }`}
                  >
                    {isMobile && value.label.length > 6 ? value.label.slice(0,6) : value.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-zinc-400 mb-2 sm:mb-3">
                 📈 Price/mo
              </label>
              <div className="grid grid-cols-4 gap-1 sm:gap-2">
                {pricePoints.map(price => (
                  <button
                    key={price}
                    onClick={() => setSelectedPrice(price)}
                    className={`px-2 py-2 rounded-lg text-xs font-medium transition-all ${
                      selectedPrice === price
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                    }`}
                  >
                    ${price}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className={`mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-zinc-800 grid ${isMobile ? 'grid-cols-2 gap-3' : 'grid-cols-5 gap-4'}`}>
            <div className="text-center">
              <p className="text-zinc-500 text-xs uppercase tracking-wider">Funding</p>
              <p className="text-lg sm:text-xl font-bold text-yellow-500 mt-1">
                {formatCompactCurrency(preSeedFunding[selectedPreSeed] + seriesAFunding[selectedSeriesA])}
              </p>
            </div>
            <div className="text-center">
              <p className="text-zinc-500 text-xs uppercase tracking-wider">Churn</p>
              <p className="text-lg sm:text-xl font-bold text-orange-500 mt-1">
                {(customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1)}%
              </p>
            </div>
            {!isMobile && (
              <>
                <div className="text-center">
                  <p className="text-zinc-500 text-xs uppercase tracking-wider">LTV</p>
                  <p className="text-lg sm:text-xl font-bold text-purple-500 mt-1">
                    ${customerLifetimes[selectedLifetime].monthlyChurn > 0 ? 
                      Math.round(selectedPrice / customerLifetimes[selectedLifetime].monthlyChurn) : 
                      (selectedPrice * 36)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-zinc-500 text-xs uppercase tracking-wider">Retention</p>
                  <p className="text-lg sm:text-xl font-bold text-blue-500 mt-1">
                    {customerLifetimes[selectedLifetime].monthlyChurn > 0 ? 
                      `${Math.round((1 - customerLifetimes[selectedLifetime].monthlyChurn) * 100)}%` : 
                      '100%'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-zinc-500 text-xs uppercase tracking-wider">Price Impact</p>
                  <p className="text-lg sm:text-xl font-bold text-green-500 mt-1">{priceMultipliers[selectedPrice]}x</p>
                </div>
              </>
            )}
          </div>
        </div>

        <div className={`flex gap-2 mb-6 sm:mb-8 ${isMobile ? 'overflow-x-auto' : ''}`}>
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all whitespace-nowrap text-sm sm:text-base ${
              activeTab === 'overview' 
                ? 'bg-blue-600 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('growth')}
            className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all whitespace-nowrap text-sm sm:text-base ${
              activeTab === 'growth' 
                ? 'bg-blue-600 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            Growth
          </button>
          <button
            onClick={() => setActiveTab('financials')}
            className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all whitespace-nowrap text-sm sm:text-base ${
              activeTab === 'financials' 
                ? 'bg-blue-600 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            Details
          </button>
        </div>

        {activeTab === 'overview' && (
          <div className="space-y-6 sm:space-y-8">
            <div className={`grid ${isMobile ? 'grid-cols-1 gap-4' : 'grid-cols-2 gap-6'}`}>
              <div className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
                <h3 className="text-base sm:text-lg font-semibold mb-4 text-green-500">Bank Balance</h3>
                <ResponsiveContainer width="100%" height={isMobile ? 250 : 350}>
                  <LineChart data={bankBalanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis 
                      dataKey="quarter" 
                      stroke="#71717a" 
                      fontSize={isMobile ? 10 : 12}
                      angle={isMobile ? -45 : 0}
                      textAnchor={isMobile ? "end" : "middle"}
                    />
                    <YAxis 
                      stroke="#71717a" 
                      tickFormatter={(value) => formatCompactCurrency(value)} 
                      fontSize={isMobile ? 10 : 12} 
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    {!isMobile && <Legend />}
                    <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="pessimistic" stroke="#ef4444" strokeWidth={2} name="Pessimistic" />
                    <Line type="monotone" dataKey="normal" stroke="#3b82f6" strokeWidth={3} name="Normal" />
                    <Line type="monotone" dataKey="optimistic" stroke="#22c55e" strokeWidth={2} name="Optimistic" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
                <h3 className="text-base sm:text-lg font-semibold mb-4 text-yellow-500">Marketing Spend</h3>
                <ResponsiveContainer width="100%" height={isMobile ? 250 : 350}>
                  <AreaChart data={adSpendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis 
                      dataKey="quarter" 
                      stroke="#71717a" 
                      fontSize={isMobile ? 10 : 12}
                      angle={isMobile ? -45 : 0}
                      textAnchor={isMobile ? "end" : "middle"}
                    />
                    <YAxis 
                      stroke="#71717a" 
                      tickFormatter={(value) => formatCompactCurrency(value)} 
                      fontSize={isMobile ? 10 : 12} 
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    {!isMobile && <Legend />}
                    <Area type="monotone" dataKey="preSeed" stackId="1" stroke="#10b981" fill="#10b981" name="Pre-seed" />
                    <Area type="monotone" dataKey="seriesA" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" name="Series A" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={`grid ${isMobile ? 'grid-cols-1 gap-4' : 'grid-cols-3 gap-6'}`}>
              {[
                { label: 'Pessimistic', data: pessimisticTotals, colorClass: 'text-red-500' },
                { label: 'Normal', data: normalTotals, colorClass: 'text-blue-500' },
                { label: 'Optimistic', data: optimisticTotals, colorClass: 'text-green-500' }
              ].map(({ label, data, colorClass }) => (
                <div key={label} className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
                  <h3 className={`text-base sm:text-lg font-semibold mb-3 sm:mb-4 ${colorClass}`}>{label}</h3>
                  <div className="space-y-3 sm:space-y-4">
                    <div>
                      <p className="text-zinc-500 text-xs uppercase">Final Users</p>
                      <p className="text-xl sm:text-2xl font-bold mt-1">{data.finalUsers.toLocaleString()}</p>
                      {!isMobile && (
                        <p className="text-xs text-zinc-400 mt-1">
                          Acq: {data.totalNewUsers.toLocaleString()} | Lost: {data.totalChurned.toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="pt-3 sm:pt-4 border-t border-zinc-800">
                      <p className="text-zinc-500 text-xs uppercase">Final Balance</p>
                      <p className={`text-xl sm:text-2xl font-bold mt-1 ${data.finalBalance >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {formatCompactCurrency(data.finalBalance)}
                      </p>
                    </div>
                    <div>
                      <p className="text-zinc-500 text-xs uppercase">ROI</p>
                      <p className={`text-lg sm:text-xl font-bold ${data.roi >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {data.roi.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'growth' && (
          <div className="space-y-6 sm:space-y-8">
            <div className={`grid ${isMobile ? 'grid-cols-1 gap-4' : 'grid-cols-2 gap-6'}`}>
              <div className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
                <h3 className="text-base sm:text-lg font-semibold mb-4 text-blue-500">
                  Active Users
                </h3>
                <ResponsiveContainer width="100%" height={isMobile ? 250 : 350}>
                  <LineChart data={userGrowthData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis 
                      dataKey="quarter" 
                      stroke="#71717a" 
                      fontSize={isMobile ? 10 : 12}
                      angle={isMobile ? -45 : 0}
                      textAnchor={isMobile ? "end" : "middle"}
                    />
                    <YAxis stroke="#71717a" fontSize={isMobile ? 10 : 12} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                    />
                    {!isMobile && <Legend />}
                    <Line type="monotone" dataKey="pessimistic" stroke="#ef4444" strokeWidth={2} name="Pessimistic" />
                    <Line type="monotone" dataKey="normal" stroke="#3b82f6" strokeWidth={3} name="Normal" />
                    <Line type="monotone" dataKey="optimistic" stroke="#22c55e" strokeWidth={2} name="Optimistic" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
                <h3 className="text-base sm:text-lg font-semibold mb-4 text-orange-500">Churn Analysis</h3>
                <div className="space-y-4">
                  <div className="bg-zinc-800 rounded-lg p-3 sm:p-4">
                    <h4 className="text-xs sm:text-sm font-medium text-zinc-400 mb-2">Current Setting</h4>
                    <p className="text-xl sm:text-2xl font-bold text-orange-400">{customerLifetimes[selectedLifetime].label}</p>
                    <p className="text-xs sm:text-sm text-zinc-500 mt-1">
                      {(customerLifetimes[selectedLifetime].monthlyChurn * 100).toFixed(1)}% monthly churn
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-zinc-800 rounded-lg p-3">
                      <p className="text-xs text-zinc-500 uppercase">LTV</p>
                      <p className="text-lg sm:text-xl font-bold text-purple-400">
                        ${customerLifetimes[selectedLifetime].monthlyChurn > 0 
                          ? Math.round(selectedPrice / customerLifetimes[selectedLifetime].monthlyChurn)
                          : selectedPrice * 36}
                      </p>
                    </div>
                    <div className="bg-zinc-800 rounded-lg p-3">
                      <p className="text-xs text-zinc-500 uppercase">CAC</p>
                      <p className="text-lg sm:text-xl font-bold text-blue-400">
                        ${Math.round((normalCAC[0] + normalCAC[11]) / 2)}
                      </p>
                    </div>
                  </div>
                  
                  {/* Debug Info */}
                  <div className="bg-zinc-800 rounded-lg p-3 text-xs">
                    <p className="text-zinc-500 uppercase mb-1">Impact (Normal Scenario)</p>
                    <p className="text-zinc-300">Total Acquired: {normalTotals.totalNewUsers.toLocaleString()}</p>
                    <p className="text-red-400">Total Churned: {normalTotals.totalChurned.toLocaleString()}</p>
                    <p className="text-green-400">Final Active: {normalTotals.finalUsers.toLocaleString()}</p>
                    <p className="text-yellow-400 mt-1">Churn Impact: {((normalTotals.totalChurned / normalTotals.totalNewUsers) * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-zinc-900 rounded-xl p-4 sm:p-6 border border-zinc-800">
              <h3 className="text-base sm:text-lg font-semibold mb-4 text-blue-500">Revenue</h3>
              <ResponsiveContainer width="100%" height={isMobile ? 250 : 300}>
                <BarChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis 
                    dataKey="quarter" 
                    stroke="#71717a" 
                    fontSize={isMobile ? 10 : 12}
                    angle={isMobile ? -45 : 0}
                    textAnchor={isMobile ? "end" : "middle"}
                  />
                  <YAxis 
                    stroke="#71717a" 
                    tickFormatter={(value) => formatCompactCurrency(value)} 
                    fontSize={isMobile ? 10 : 12} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  {!isMobile && <Legend />}
                  <Bar dataKey="pessimistic" fill="#ef4444" name="Pessimistic" />
                  <Bar dataKey="normal" fill="#3b82f6" name="Normal" />
                  <Bar dataKey="optimistic" fill="#22c55e" name="Optimistic" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'financials' && (
          <div className="space-y-4 sm:space-y-6">
            {isMobile ? (
              <div className="space-y-4">
                {normalData.slice(0, 6).map((row, idx) => (
                  <div key={idx} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                    <div className="flex justify-between items-center mb-3">
                      <span className="font-semibold text-blue-400">{row.quarter}</span>
                      <span className={`font-bold ${row.bankBalance >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {formatCompactCurrency(row.bankBalance)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-zinc-500">Active</p>
                        <p className="font-medium">{row.activeUsers.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Revenue</p>
                        <p className="font-medium">{formatCompactCurrency(row.revenue)}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">New</p>
                        <p className="font-medium">+{row.newUsers}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Churned</p>
                        <p className="font-medium text-red-400">-{row.churnedUsers}</p>
                      </div>
                    </div>
                  </div>
                ))}
                <p className="text-center text-zinc-500 text-sm">Showing first 6 quarters</p>
              </div>
            ) : (
              [
                { data: normalData, title: 'Normal Scenario', colorClass: 'text-blue-500' },
                { data: pessimisticData, title: 'Pessimistic Scenario', colorClass: 'text-red-500' },
                { data: optimisticData, title: 'Optimistic Scenario', colorClass: 'text-green-500' }
              ].map(({ data, title, colorClass }) => (
                <div key={title} className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
                  <div className="px-6 py-4 bg-zinc-950 border-b border-zinc-800">
                    <h3 className={`text-lg font-semibold ${colorClass}`}>{title}</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-zinc-950/50">
                        <tr>
                          <th className="px-4 py-3 text-left text-zinc-400">Quarter</th>
                          <th className="px-4 py-3 text-right text-zinc-400">New Users</th>
                          <th className="px-4 py-3 text-right text-zinc-400">Active</th>
                          <th className="px-4 py-3 text-right text-zinc-400">Churned</th>
                          <th className="px-4 py-3 text-right text-zinc-400">LTV/CAC</th>
                          <th className="px-4 py-3 text-right text-zinc-400">Revenue</th>
                          <th className="px-4 py-3 text-right text-zinc-400">Balance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((row, idx) => (
                          <tr key={idx} className="border-t border-zinc-800 hover:bg-zinc-800/50">
                            <td className="px-4 py-3">{row.quarter}</td>
                            <td className="px-4 py-3 text-right">+{row.newUsers.toLocaleString()}</td>
                            <td className="px-4 py-3 text-right font-medium">{row.activeUsers.toLocaleString()}</td>
                            <td className="px-4 py-3 text-right text-red-400">
                              {row.churnedUsers > 0 ? `-${row.churnedUsers.toLocaleString()}` : '-'}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <span className={`font-medium ${
                                row.ltvCacRatio > 3 ? 'text-green-400' : 
                                row.ltvCacRatio > 1 ? 'text-yellow-400' : 'text-red-400'
                              }`}>
                                {row.ltvCacRatio.toFixed(1)}x
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right">{formatCurrency(row.revenue)}</td>
                            <td className={`px-4 py-3 text-right font-bold ${
                              row.bankBalance >= 0 ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {formatCurrency(row.bankBalance)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NormScoutBusinessPlan;